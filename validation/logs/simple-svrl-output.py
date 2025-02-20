from lxml import etree

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

n = 0
for item in failed_assertions_details:
    n += 1
    print(n)
    print("\nSeverity:")
    print(item["role"])
    print("\nMessage:")
    print(item["message"])
    print("\nContext:")
    print(item["location"])
    print("\nTest:")
    print(item["test"])
    print("--------------------------------------------------")
