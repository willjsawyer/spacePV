import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="LCOE Space Solar Analysis",
    page_icon="☀️",
    layout="wide"
)

st.title("LCOE Space Solar Cost Model Analysis")

# Sidebar for inputs
st.sidebar.header("Input Parameters")

# 1. Discount Rate slider
discount_rate = st.sidebar.slider(
    "Discount Rate (%)",
    min_value=1.0,
    max_value=15.0,
    value=7.7,
    step=0.1,
    key="discount_rate"
)

# 2. Project lifetime textbox (positive integers only)
project_duration_input = st.sidebar.text_input(
    "Project lifetime (years)",
    value="10",
    key="project_duration_input"
)

# Validate and convert project duration
try:
    project_duration = int(project_duration_input)
    if project_duration <= 0:
        st.sidebar.error("Project lifetime must be a positive integer")
        project_duration = 10  # Default fallback
except ValueError:
    st.sidebar.error("Please enter a valid positive integer")
    project_duration = 10  # Default fallback

# 3. Solar irradiance dropdown
solar_irr_option = st.sidebar.selectbox(
    "Solar Irradiance",
    options=["32.6 kWh/m2/day (space)", "5.5 kWh/m2/day (terrestrial)"],
    key="power_gen_rate"
)

# Map dropdown to numeric value
solar_irr_rate = 5.5 if solar_irr_option == "5.5 kWh/m2/day (terrestrial)" else 32.6

# PV panel type dropdown
panel_type_option = st.sidebar.selectbox(
    "PV panel type",
    options=["commercial terrestrial (monocrystalline Si)", "Space-based (multi-junction GaAs)"],
    key="panel_type"
)

# Define panel efficiency based on panel type (in %)
panel_eff = 0.21 if panel_type_option == "commercial terrestrial (monocrystalline Si)" else 0.32

# define the power generation rate (kWh/m2/day)
power_gen_rate = panel_eff * solar_irr_rate

# 4. Launch Mass slider
launch_mass = st.sidebar.slider(
    "Launch mass (kg/m2)",
    min_value=0.1,
    max_value=10.0,
    value=2.0,
    step=0.1,
    key="launch_mass"
)

# Display current values
st.sidebar.markdown("---")
st.sidebar.markdown("### Current Values")
st.sidebar.write(f"Discount Rate: {discount_rate:.1f}%")
st.sidebar.write(f"Project Lifetime: {project_duration} years")
st.sidebar.write(f"Power Generation: {power_gen_rate} kWh/day")
st.sidebar.write(f"Launch Mass: {launch_mass:.2f} kg/m²")

# LCOE calculation function
def calculate_lcoe(launch_cost_grid, array_cost_grid, project_duration, discount_rate):
    # lifetime_cost is the total cost per m^2: launch cost plus array cost grid (all $/m^2)
    # panel eff * 1000 W/m^2 standard incident is the standard output W/m2. times $/W gives array cost per m^2
    lifetime_cost = (launch_cost_grid * launch_mass) + (array_cost_grid * panel_eff * 1000)  # $/m^2

    # Calculate lifetime energy output per m^2 (kWh) using discounted sum over project duration
    # power_gen_rate is kWh/m^2/day; multiply by 365 for annual; discount for each year
    years = np.arange(1, project_duration + 1)
    discount_factors = 1 / (1 + (discount_rate / 100)) ** years
    lifetime_energy = np.sum(power_gen_rate * 365 * discount_factors)

    lcoe = lifetime_cost / lifetime_energy
    return lcoe

# Generate data for surface plot
# X-axis: Launch Cost ($/kg) - log scale from 100 to 10,000
launch_cost_min = 100
launch_cost_max = 5000
launch_cost_points = np.logspace(np.log10(launch_cost_min), np.log10(launch_cost_max), 50)

# Y-axis: Array Cost ($/W) - log scale from 1 to 1000
array_cost_min = 1
array_cost_max = 1000
array_cost_points = np.logspace(np.log10(array_cost_min), np.log10(array_cost_max), 50)

# Create meshgrid
launch_cost_grid, array_cost_grid = np.meshgrid(launch_cost_points, array_cost_points)

# Calculate LCOE for all combinations
lcoe_grid = calculate_lcoe(
    launch_cost_grid,
    array_cost_grid,
    project_duration,
    discount_rate
)

# Create 2D heatmap plot
fig = go.Figure()

# Add heatmap
fig.add_trace(go.Heatmap(
    z=lcoe_grid,
    x=launch_cost_grid[0, :],  # X-axis values (Launch Cost)
    y=array_cost_grid[:, 0],  # Y-axis values (Array Cost)
    colorscale='Viridis',
    hovertemplate='Launch Cost: $%{x:.2f}/kg<br>Array Cost: $%{y:.2f}/W<br>LCOE: $%{z:.4f}/W<extra></extra>',
    colorbar=dict(title="LCOE ($/kWh)"),
    showscale=True
))

# Add invisible scatter points for click detection
# Flatten the grids for scatter plot
launch_cost_flat = launch_cost_grid.flatten()
array_cost_flat = array_cost_grid.flatten()
lcoe_flat = lcoe_grid.flatten()

fig.add_trace(go.Scatter(
    x=launch_cost_flat,
    y=array_cost_flat,
    mode='markers',
    marker=dict(size=10, opacity=0, symbol='circle'),  # Invisible but clickable markers
    hovertemplate='Launch Cost: $%{x:.2f}/kg<br>Array Cost: $%{y:.2f}/W<br>LCOE: $%{customdata:.4f}/W<extra></extra>',
    customdata=lcoe_flat,
    name='click_points',
    legendgroup='click_points',
    showlegend=False
))

fig.update_layout(
    title='LCOE Heatmap',
    xaxis=dict(
        title='Launch Cost ($/kg)',
        type='log'
    ),
    yaxis=dict(
        title='Array Cost ($/W)',
        type='log'
    ),
    width=900,
    height=700,
    margin=dict(l=0, r=0, t=50, b=0)
)

# Initialize session state for selected point
if 'selected_point' not in st.session_state:
    st.session_state.selected_point = None

# Display the plot with click selection
event = st.plotly_chart(
    fig, 
    use_container_width=True,
    on_select="rerun",
    key="lcoe_plot"
)

# Process selection from event
if event and 'selection' in event:
    selection = event['selection']
    if selection and 'points' in selection:
        points = selection['points']
        if points:
            # Get the first selected point
            point = points[0]
            selected_launch_cost = point.get('x', 0)
            selected_array_cost = point.get('y', 0)
            
            # Try to get LCOE from customdata (if from scatter point)
            selected_lcoe = point.get('customdata', None)
            
            # If not from scatter point, calculate from grid
            if selected_lcoe is None:
                launch_idx = np.argmin(np.abs(launch_cost_points - selected_launch_cost))
                cost_idx = np.argmin(np.abs(array_cost_points - selected_array_cost))
                selected_lcoe = lcoe_grid[cost_idx, launch_idx]
            
            st.session_state.selected_point = {
                'launch_cost': selected_launch_cost,
                'array_cost': selected_array_cost,
                'lcoe': selected_lcoe
            }

# Display selected point values below the plot
if st.session_state.selected_point:
    st.markdown("---")
    st.markdown("### Selected Point")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Launch Cost", f"${st.session_state.selected_point['launch_cost']:.2f}/kg")
    with col2:
        st.metric("Array Cost", f"${st.session_state.selected_point['array_cost']:.2f}/W")
    with col3:
        st.metric("LCOE", f"${st.session_state.selected_point['lcoe']:.4f}/W")

# Key variable descriptions
st.markdown("---")
st.markdown("### Key Variable Descriptions")
st.markdown("""
Project lifetime and discount rate: Lazard's [LCOE analysis](https://www.lazard.com/research-insights/levelized-cost-of-energyplus-lcoeplus/) for utility-scale solar PV uses a 35 year project lifetime and a 7.7% discount rate. A project lifetime of 10 years may be more appropriate, matching the typical lifetime of commerical LEO satellites. 

Solar Irradiance: A typical southwest US location sees an annualized average irradiance of 5.5 kWh/m2/day, accounting for day/night cycles, weather, and the absorption of portions of the solar spectrum by the atmosphere [NREL](https://www.nrel.gov/gis/solar-resource-maps). In space, assume the [AM0](https://www.pveducation.org/pvcdrom/appendices/standard-solar-spectra) solar spectrum (1366 W/m2) and (optimistically) 24 hours of sunlight a day year-round. 

PV panel type: Panel efficiency is assumed to be 21% for monocrystalline Si and 32% for multi-junction GaAs. Efficiency will be reduced at the elevated temperature expected. 

Launch mass: The launch mass is, at minimum, the panel mass. Mechanical structure, wiring, and the mass of the electricity user, etc. will increase this. A terrestrial solar panel (e.g. design for mounting on a roof) might weigh [10](https://freedomsolarpower.com/blog/solar-panel-weight-guide) - [20](https://www.greenmatch.co.uk/solar-energy/solar-panels/sizes) kg/m^2 -- not including any additional structure. Current space-ready PV panels weigh ~2 kg/m^2 ([A](https://blueskies.nianet.org/wp-content/uploads/2023-Blue-Skies-Final-Research-Paper-University-of-Texas-Austin.pdf), [B](https://magazine.caltech.edu/post/sspp-space-solar-power-project)). Research targets for lightweight panels are as low as 0.05 kg/m^2 (requiring T.B.D. new technology) to 0.25 kg/m^2 (existing [thin-film](https://blueskies.nianet.org/wp-content/uploads/2023-Blue-Skies-Final-Research-Paper-University-of-Texas-Austin.pdf) with durability concerns?)

Array cost: For existing space-base PV, cost estimates range from [\$31](https://magazine.caltech.edu/post/sspp-space-solar-power-project) per Watt for manufacturing GaAs cells to [\$700--1000](https://ntrs.nasa.gov/api/citations/20205002844/downloads/Solar%20Power%20Generation_2.pdf) per Watt for the entire array. Terrestrial installations have hardware costs of the order [\$1](https://www.energy.gov/eere/solar/solar-photovoltaic-system-cost-benchmarks) per W, while the panels or modules themselves are only [\$0.25](https://ourworldindata.org/grapher/solar-pv-prices) per Watt.

Launch cost: Currently in the range \$1000--5000 per kg with projections down to \$100 for launch to LEO.

My conclusions: The default values are my optimistic assumptions for a near-future space-based deployment of monocrystalline Si panels. If one assumes an array capital ocst that is similar to terrestrial use and a reduction in launch costs to $100/kg, then the LCOE is similar to that of terrestrial solar PV, of the order cents per kWh. 
A major uncertainty, to me, is the durability of 'normal' PV cells in a space environment, subject to increased UV light, radiation, and elevated temperature. 

""")

