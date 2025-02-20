import subprocess
from pathlib import Path
from lxml import etree
from saxonche import PySaxonProcessor
from rich.console import Console
from rich.table import Table

# define the base directory and file paths
base_dir = Path(__file__).parent.parent
xslt_path = (
    base_dir / "validation" / "schema" / "CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.xsl"
)
svrl_output_path = base_dir / "validation" / "logs" / "svrl-output.xml"


def parse_svrl(svrl_result):
    # parse the svrl result string
    svrl_doc = etree.fromstring(svrl_result.encode("utf-8"))

    # namespace map for finding elements
    ns = {
        "svrl": "http://purl.oclc.org/dsdl/svrl",
        "sch": "http://purl.oclc.org/dsdl/schematron",
    }

    # extract all failed assertions
    results = []
    for assertion in svrl_doc.xpath(".//svrl:failed-assert", namespaces=ns):
        fired_rule = assertion.xpath(
            "preceding-sibling::svrl:fired-rule[1]", namespaces=ns
        )
        role = fired_rule[0].get("role") if fired_rule else "Role not found or missing"

        text_element = assertion.find("svrl:text", namespaces=ns)
        text = text_element.text.strip() if text_element is not None else "No message"
        location = assertion.get("location", "No context provided").strip()
        test = assertion.get("test", "No test provided").strip()

        results.append(
            {"severity": role, "message": text, "context": location, "test": test}
        )
    return results


def display_svrl(validation_results, console):
    # create a Rich table with the specified format
    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    table.add_column("Severity", style="dim", width=12)
    table.add_column("Message", style="dim", width=52)
    table.add_column("Context", style="dim", width=52)
    table.add_column("Test", style="dim", width=52)

    # add rows to the table
    for result in validation_results:
        style = (
            "bright_red"
            if "error" in result["severity"].lower()
            else "orange1"
            if "warning" in result["severity"].lower()
            else ""
        )
        table.add_row(
            result["severity"],
            result["message"],
            result["context"],
            result["test"],
            style=style,
        )

    # display the table
    console.print(table)


def display_summary(validation_results, console):
    errors = [res for res in validation_results if "error" in res["severity"].lower()]
    warnings = [
        res for res in validation_results if "warning" in res["severity"].lower()
    ]

    console.print(f"Total Errors: {len(errors)}", style="bold bright_red")
    console.print(f"Total Warnings: {len(warnings)}", style="bold orange1")

    if len(errors) > 0:
        console.print("Validation Failed Due to Errors", style="bold bright_red")
    else:
        (
            console.print("Validation Passed with Warnings", style="bold green1")
            if warnings
            else console.print("Validation Passed", style="bold green1")
        )


def validate_xml_with_schematron(xml_path):
    console = Console()
    with PySaxonProcessor(license=False) as processor:
        xslt_processor = processor.new_xslt30_processor()
        try:
            compiled_stylesheet = xslt_processor.compile_stylesheet(
                stylesheet_file=str(xslt_path)
            )
            console.print("Stylesheet compiled successfully.", style="bold green1")
        except Exception as e:
            console.print(
                f"Error during stylesheet compilation: {str(e)}",
                style="bold bright_red",
            )
            return

        try:
            result = compiled_stylesheet.transform_to_string(source_file=str(xml_path))
            if result:
                console.print("Transformation successful.", style="bold green1")
                console.print("Saving to logs/svrl-output.xml.", style="bold green1")
                with open(svrl_output_path, "w") as f:
                    f.write(result)
                validation_results = parse_svrl(result)
                display_svrl(validation_results, console)
                display_summary(validation_results, console)
            else:
                console.print(
                    "No output was generated from the transformation.",
                    style="bold bright_red",
                )
        except Exception as e:
            console.print(
                f"Error during transformation: {str(e)}", style="bold bright_red"
            )


def main():
    data_directory = base_dir / "tests" / "assets"

    try:
        fzf_command = [
            "fzf",
            "--prompt=select an eICR XML file: ",
            "--height=50%",
            "--layout=reverse",
            "--border",
            "--exit-0",
            "--ansi",
        ]

        result = subprocess.run(
            fzf_command, stdout=subprocess.PIPE, text=True, cwd=data_directory
        )
        selected_file = result.stdout.strip()

        if not selected_file:
            print("No file selected")
            return

        xml_path = data_directory / selected_file
        validate_xml_with_schematron(xml_path=str(xml_path))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
