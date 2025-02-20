from lxml import etree
from rich.console import Console
from rich.table import Table

# load the svrl output file
tree = etree.parse("svrl-output.xml")
root = tree.getroot()

# define namespaces
namespaces = {"svrl": "http://purl.oclc.org/dsdl/svrl"}

# list to hold all failed assertions with additional details
failed_assertions_details = []

# iterate over all failed assertions
for failed_assert in root.xpath("//svrl:failed-assert", namespaces=namespaces):
    # find the nearest preceding fired-rule using xpath
    fired_rule = failed_assert.xpath(
        "preceding-sibling::svrl:fired-rule[1]", namespaces=namespaces
    )
    if fired_rule:
        role = fired_rule[0].get("role")
    else:
        role = "Role not found or missing"

    # collect information from the failed assertion
    details = {
        "role": role,
        "message": failed_assert.find(".//svrl:text", namespaces=namespaces).text,
        "location": failed_assert.get("location"),
        "test": failed_assert.get("test"),
    }
    failed_assertions_details.append(details)

# setup Rich console
console = Console()

# create a table
table = Table(show_lines=True)

# add columns
table.add_column("Role", style="bold")
table.add_column("Message")
table.add_column("Context", header_style="bold cyan")
table.add_column("Test", style="dim")

# add rows to the table with color coding based on the role
for item in failed_assertions_details:
    style = (
        "bright_red"
        if "error" in item["role"].lower()
        else "orange1"
        if "warning" in item["role"].lower()
        else ""
    )
    table.add_row(
        item["role"], item["message"], item["location"], item["test"], style=style
    )

# print the table
console.print(table)
