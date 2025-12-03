import pandas as pd
import plotly.express as px
import streamlit as st
import io

# LOAD DATA CORRECTLY 
with open("cloudmart_multi_account.csv", 'r') as f:
    content = f.read()

# Removing outer quotes from each line
lines = content.split('\n')
cleaned_lines = [line.strip('"') for line in lines if line.strip()]
cleaned_csv = '\n'.join(cleaned_lines)

# Read cleaned CSV
df = pd.read_csv(io.StringIO(cleaned_csv))
df.columns = df.columns.str.strip()

# Convert MonthlyCostUSD to numeric
df['MonthlyCostUSD'] = pd.to_numeric(df['MonthlyCostUSD'], errors='coerce')

# Keep original for before/after comparison
df_original = df.copy()

st.set_page_config(page_title="CloudMart Dashboard", layout="wide")
st.title("CloudMart Multi-Account Resource Tagging Dashboard")
st.markdown("---")

# TASK SET 1: DATA EXPLORATION 
st.header("Task Set 1: Data Exploration")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Resources", len(df))
with col2:
    tagged_count = (df['Tagged'] == 'Yes').sum()
    st.metric("Tagged Resources", tagged_count)
with col3:
    untagged_count = (df['Tagged'] == 'No').sum()
    st.metric("Untagged Resources", untagged_count)

st.subheader("1.1 - First 5 Rows of Dataset")
st.dataframe(df.head(5), use_container_width=True)

st.subheader("1.2 - Missing Values Analysis")
missing = df.isnull().sum()
st.write(missing[missing > 0] if missing.sum() > 0 else "✓ No critical missing values")

st.subheader("1.3 - Columns with Most Missing Values")
missing_sorted = missing[missing > 0].sort_values(ascending=False)
if len(missing_sorted) > 0:
    st.bar_chart(missing_sorted)
else:
    st.info("No missing values detected")

st.subheader("1.4 - Total Resources: Tagged vs Untagged Count")
tagged_counts = df['Tagged'].value_counts()
st.write(tagged_counts)
st.bar_chart(tagged_counts)

st.subheader("1.5 - Percentage of Untagged Resources")
untagged = df[df['Tagged'] == "No"].shape[0]
total = df.shape[0]
percent_untagged = (untagged / total * 100) if total > 0 else 0
st.metric("% Untagged Resources", f"{percent_untagged:.2f}%")

# TASK SET 2: COST VISIBILITY 
st.header("2️.Task Set 2: Cost Visibility")

col1, col2, col3 = st.columns(3)

with col1:
    total_cost = df["MonthlyCostUSD"].sum()
    st.metric("Total Monthly Cost", f"${total_cost:,.2f}")

with col2:
    untagged_cost = df[df['Tagged'] == "No"]["MonthlyCostUSD"].sum()
    st.metric("Untagged Cost ($)", f"${untagged_cost:,.2f}")

with col3:
    tagged_cost = df[df['Tagged'] == "Yes"]["MonthlyCostUSD"].sum()
    st.metric("Tagged Cost ($)", f"${tagged_cost:,.2f}")

st.subheader("2.1 - Total Cost of Tagged vs Untagged Resources")
cost_by_tag = df.groupby("Tagged")["MonthlyCostUSD"].sum()
st.bar_chart(cost_by_tag)
st.write(cost_by_tag)

st.subheader("2.2 - Percentage of Total Cost that is Untagged")
percent_untagged_cost = (untagged_cost / total_cost * 100) if total_cost > 0 else 0
st.metric("% Untagged Cost", f"{percent_untagged_cost:.2f}%")

st.subheader("2.3 - Department with Most Untagged Cost")
untagged_by_dept = df[df['Tagged'] == "No"].groupby("Department")["MonthlyCostUSD"].sum()
if len(untagged_by_dept) > 0:
    most_untagged_dept = untagged_by_dept.idxmax()
    most_untagged_cost = untagged_by_dept.max()
    st.write(f"**{most_untagged_dept}** has the most untagged cost: **${most_untagged_cost:,.2f}**")
    st.bar_chart(untagged_by_dept)
else:
    st.info("No untagged resources found")

st.subheader("2.4 - Project with Highest Total Cost Overall")
project_cost = df.groupby("Project")["MonthlyCostUSD"].sum()
highest_cost_project = project_cost.idxmax()
highest_cost_value = project_cost.max()
st.write(f"**{highest_cost_project}** consumes the most cost: **${highest_cost_value:,.2f}**")
st.bar_chart(project_cost)

st.subheader("2.5 - Prod vs Dev Environment: Cost and Tagging Quality")
env_tagged = df.groupby(["Environment", "Tagged"])["MonthlyCostUSD"].sum().reset_index()
fig = px.bar(env_tagged, x="Environment", y="MonthlyCostUSD", color="Tagged", 
             barmode="group", title="Cost by Environment and Tagging Status")
st.plotly_chart(fig, use_container_width=True)
st.write(env_tagged)

# TASK SET 3: TAGGING COMPLIANCE
st.header("Task Set 3: Tagging Compliance")

tag_fields = ["Department", "Project", "Owner", "CostCenter", "CreatedBy"]
df["TagScore"] = df[tag_fields].notnull().sum(axis=1)

st.subheader("3.1 - Tag Completeness Score Per Resource")
st.info(f"Tag Completeness Score = number of tag fields (out of {len(tag_fields)}) that are non-empty")

st.subheader("3.2 - Top 5 Resources with Lowest Tag Completeness")
lowest_compliance = df.sort_values(by="TagScore")[["ResourceID", "Service", "Department", "TagScore", "MonthlyCostUSD"]].head(5)
st.dataframe(lowest_compliance, use_container_width=True)

st.subheader("3.3 - Most Frequently Missing Tag Fields")
missing_tags = df[tag_fields].isnull().sum().sort_values(ascending=False)
st.bar_chart(missing_tags)
st.write(missing_tags)

untagged_df = df[df["Tagged"] == "No"].copy()

st.subheader("3.4 - List All Untagged Resources and Their Costs")
st.dataframe(untagged_df[["ResourceID", "Service", "Department", "MonthlyCostUSD", "Tagged"]], 
             use_container_width=True)
total_untagged_cost = untagged_df["MonthlyCostUSD"].sum()
st.metric("Total Cost of Untagged Resources", f"${total_untagged_cost:,.2f}")

st.subheader("3.5 - Export Untagged Resources (Original)")
original_untagged_csv = untagged_df.to_csv(index=False)
st.download_button(
    label="Download untagged.csv (Original)",
    data=original_untagged_csv,
    file_name="untagged.csv",
    mime="text/csv"
)

# TASK SET 4: VISUALIZATION DASHBOARD 
st.header("Task Set 4: Visualization Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.subheader("4.1 - Tagged vs Untagged Resources")
    fig1 = px.pie(df, names="Tagged", title="Resource Count: Tagged vs Untagged", hole=0.3)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("4.4 - Cost by Environment (Prod/Dev/Test)")
    env_cost = df.groupby("Environment")["MonthlyCostUSD"].sum().reset_index()
    fig_env = px.pie(env_cost, names="Environment", values="MonthlyCostUSD", 
                     title="Cost Distribution by Environment", hole=0.3)
    st.plotly_chart(fig_env, use_container_width=True)

st.subheader("4.2 - Cost per Department by Tagging Status")
dept_cost = df.groupby(["Department", "Tagged"])["MonthlyCostUSD"].sum().reset_index()
fig2 = px.bar(dept_cost, x="Department", y="MonthlyCostUSD", color="Tagged", 
              barmode="group", title="Cost by Department and Tagging Status")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("4.3 - Horizontal Bar Chart: Total Cost per Service")
cost_by_service = df.groupby("Service")["MonthlyCostUSD"].sum().reset_index().sort_values("MonthlyCostUSD", ascending=True)
fig3 = px.bar(cost_by_service, x="MonthlyCostUSD", y="Service", orientation='h', 
              title="Total Cost by Service", labels={"MonthlyCostUSD": "Monthly Cost (USD)"})
st.plotly_chart(fig3, use_container_width=True)

st.subheader("4.5 - Interactive Filters (Service, Region, Department)")
col1, col2, col3 = st.columns(3)

with col1:
    service_filter = st.multiselect("Filter by Service", sorted(df["Service"].unique()), default=["EC2"])

with col2:
    region_filter = st.multiselect("Filter by Region", sorted(df["Region"].unique()))

with col3:
    dept_filter = st.multiselect("Filter by Department", sorted(df["Department"].dropna().unique()))

# Apply filters
filtered_df = df.copy()
if service_filter:
    filtered_df = filtered_df[filtered_df["Service"].isin(service_filter)]
if region_filter:
    filtered_df = filtered_df[filtered_df["Region"].isin(region_filter)]
if dept_filter:
    filtered_df = filtered_df[filtered_df["Department"].isin(dept_filter)]

st.write(f"**Filtered Results:** {len(filtered_df)} resources")
st.dataframe(filtered_df, use_container_width=True)
st.metric("Filtered Total Cost", f"${filtered_df['MonthlyCostUSD'].sum():,.2f}")

#TASK SET 5: TAG REMEDIATION WORKFLOW
st.header("Task Set 5: Tag Remediation Workflow")

st.subheader("5.1 & 5.2 - Edit Untagged Resources (Simulate Remediation)")
st.info("Manually fill in missing tags (Department, Project, Owner) to simulate tagging remediation")
editable_df = st.data_editor(untagged_df, use_container_width=True, num_rows="dynamic", key="remediation_editor")

st.subheader("5.3 - Download Updated Dataset")
col1, col2 = st.columns(2)

with col1:
    remediated_csv = editable_df.to_csv(index=False)
    st.download_button(
        label="Download remediated.csv",
        data=remediated_csv,
        file_name="remediated.csv",
        mime="text/csv"
    )

with col2:
    # Combine remediated untagged resources with still-tagged resources
    tagged_df = df[df["Tagged"] == "Yes"].copy()
    full_remediated = pd.concat([tagged_df, editable_df], ignore_index=True)
    full_remediated_csv = full_remediated.to_csv(index=False)
    st.download_button(
        label="Download original.csv (full dataset before)",
        data=df_original.to_csv(index=False),
        file_name="original.csv",
        mime="text/csv"
    )

st.subheader("5.4 - Compare Cost Visibility: Before vs After Remediation")

col1, col2, col3 = st.columns(3)

# BEFORE metrics
before_untagged_count = (df_original["Tagged"] == "No").sum()
before_untagged_cost = df_original[df_original["Tagged"] == "No"]["MonthlyCostUSD"].sum()
before_untagged_pct_cost = (before_untagged_cost / df_original["MonthlyCostUSD"].sum() * 100) if df_original["MonthlyCostUSD"].sum() > 0 else 0

# AFTER metrics (using editable_df which may have been updated by user)
after_untagged_count = (editable_df["Tagged"] == "No").sum()
after_untagged_cost = editable_df[editable_df["Tagged"] == "No"]["MonthlyCostUSD"].sum()
after_untagged_pct_cost = (after_untagged_cost / editable_df["MonthlyCostUSD"].sum() * 100) if editable_df["MonthlyCostUSD"].sum() > 0 else 0

with col1:
    st.metric("Before: Untagged Count", before_untagged_count)
    st.metric("After: Untagged Count", after_untagged_count)
    st.metric("Change", after_untagged_count - before_untagged_count)

with col2:
    st.metric("Before: Untagged Cost", f"${before_untagged_cost:,.2f}")
    st.metric("After: Untagged Cost", f"${after_untagged_cost:,.2f}")
    st.metric("Cost Improvement", f"${before_untagged_cost - after_untagged_cost:,.2f}")

with col3:
    st.metric("Before: % Untagged Cost", f"{before_untagged_pct_cost:.2f}%")
    st.metric("After: % Untagged Cost", f"{after_untagged_pct_cost:.2f}%")
    st.metric("% Point Improvement", f"{before_untagged_pct_cost - after_untagged_pct_cost:.2f}%")

st.subheader("Tagging Status Comparison Chart")
comparison_data = pd.DataFrame({
    'Metric': ['Untagged Count', 'Untagged Count'],
    'Status': ['Before', 'After'],
    'Value': [before_untagged_count, after_untagged_count]
})
fig_comparison = px.bar(comparison_data, x='Metric', y='Value', color='Status', 
                        title="Remediation Impact: Untagged Resources Before vs After",
                        barmode='group')
st.plotly_chart(fig_comparison, use_container_width=True)

# SUMMARY SECTION 
st.markdown("---")
st.header("Summary & Key Findings")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.subheader("Current State (Before Remediation)")
    st.write(f"""
    - **Total Resources:** {len(df_original)}
    - **Tagged Resources:** {(df_original['Tagged'] == 'Yes').sum()}
    - **Untagged Resources:** {before_untagged_count} ({(before_untagged_count/len(df_original)*100):.2f}%)
    - **Total Monthly Cost:** ${df_original['MonthlyCostUSD'].sum():,.2f}
    - **Untagged Cost:** ${before_untagged_cost:,.2f} ({before_untagged_pct_cost:.2f}% of total)
    """)

with summary_col2:
    st.subheader("Target State (After Remediation)")
    st.write(f"""
    - **Total Resources:** {len(editable_df)}
    - **Tagged Resources:** {(editable_df['Tagged'] == 'Yes').sum()}
    - **Untagged Resources:** {after_untagged_count} ({(after_untagged_count/len(editable_df)*100):.2f}%)
    - **Total Monthly Cost:** ${editable_df['MonthlyCostUSD'].sum():,.2f}
    - **Untagged Cost:** ${after_untagged_cost:,.2f} ({after_untagged_pct_cost:.2f}% of total)
    """)

st.markdown("---")
