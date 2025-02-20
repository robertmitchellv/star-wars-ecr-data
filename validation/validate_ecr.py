import subprocess
from pathlib import Path
from lxml import etree
from saxonche import PySaxonProcessor
from rich.console import Console
from rich.table import Table

# define the base directory and file paths
base_dir = Path(__file__).parent.parent
eicr_xslt_path = (
    base_dir
    / "validation"
    / "schema"
    / "eicr"
    / "CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.xsl"
)
rr_xslt_path = (
    base_dir
    / "validation"
    / "schema"
    / "rr"
    / "CDAR2_IG_PHCR_R2_RR_D1_2017DEC_SCHEMATRON.xsl"
)
svrl_output_path = base_dir / "validation" / "logs" / "svrl-output.xml"


def determine_document_type(xml_path):
    """
    Determine if the XML is an eICR or RR document by checking the LOINC code
    """
    console = Console()

    # show the user the selected file so they can see what was the file
    # was determined to be so they can spot check
    console.print(f"Selected file: {xml_path}")

    try:
        tree = etree.parse(str(xml_path))
        root = tree.getroot()

        # Define namespace map
        nsmap = {
            "hl7": "urn:hl7-org:v3",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }

        # Look for the code element
        code_element = root.xpath("//hl7:code/@code", namespaces=nsmap)

        if not code_element:
            console.print("✗ No LOINC code found in document", style="bold bright_red")
            return None, None

        loinc_code = code_element[0]

        # RR specific LOINC code: 88085-6
        if loinc_code == "88085-6":
            console.print(
                "✓ Successfully identified document as RR (LOINC: 88085-6)",
                style="bold green1",
            )
            return "rr", rr_xslt_path
        # eICR specific LOINC code: 55751-2
        elif loinc_code == "55751-2":
            console.print(
                "✓ Successfully identified document as eICR (LOINC: 55751-2)",
                style="bold green1",
            )
            return "eicr", eicr_xslt_path
        else:
            console.print(
                f"✗ Unknown document type - found LOINC code: {loinc_code}",
                style="bold bright_red",
            )
            return None, None

    except Exception as e:
        console.print(
            f"✗ Error determining document type: {str(e)}", style="bold bright_red"
        )
        return None, None


def parse_svrl(svrl_result):
    svrl_doc = etree.fromstring(svrl_result.encode("utf-8"))
    ns = {"svrl": "http://purl.oclc.org/dsdl/svrl"}

    results = []
    for assertion in svrl_doc.xpath(".//svrl:failed-assert", namespaces=ns):
        text_element = assertion.find("svrl:text", namespaces=ns)
        message = (
            text_element.text.strip() if text_element is not None else "No message"
        )

        # check the start of the message to determine primary rule type
        # this will prevent SHOULD rules that contain a mention of SHALL
        # from being catagorized as errors
        first_word = message.split()[0] if message else ""

        # determine severity from first word or initial phrase
        if first_word == "SHALL":
            severity = "ERROR"
        elif message.startswith("SHOULD") or "SHOULD contain" in message:
            severity = "WARNING"
        elif first_word == "MAY":
            severity = "INFO"
        # If none of the above, check for SHALL/SHOULD anywhere in message
        elif "SHALL" in message and "SHOULD" not in message:
            severity = "ERROR"
        elif "SHOULD" in message:
            severity = "WARNING"
        else:
            severity = "UNKNOWN"

        results.append(
            {
                "severity": severity,
                "message": message,
                "context": assertion.get("location", "No context"),
                "test": assertion.get("test", "No test"),
                "id": assertion.get("id", "No ID"),
            }
        )

    return results


def display_svrl(validation_results, console):
    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    table.add_column("Severity", style="dim", width=12)
    table.add_column("Message", style="dim", width=52)
    table.add_column("Context", style="dim", width=52)
    table.add_column("Test", style="dim", width=52)

    for result in validation_results:
        severity = result["severity"]
        style = (
            "bright_red"
            if severity in ["ERROR", "FATAL"]
            else "orange1"
            if severity == "WARNING"
            else "blue"
            if severity == "INFO"
            else "dim"
        )
        table.add_row(
            severity, result["message"], result["context"], result["test"], style=style
        )

    console.print(table)


def display_summary(validation_results, console):
    # count both ERROR and FATAL as errors
    errors = [
        res for res in validation_results if res["severity"] in ["ERROR", "FATAL"]
    ]
    warnings = [res for res in validation_results if res["severity"] == "WARNING"]
    infos = [res for res in validation_results if res["severity"] == "INFO"]

    console.print(f"Total Errors: {len(errors)}", style="bold bright_red")
    console.print(f"Total Warnings: {len(warnings)}", style="bold orange1")
    # only show info count if there are any
    if infos:
        console.print(f"Total Info: {len(infos)}", style="bold blue")

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

    # determine document type and get appropriate xsl
    doc_type, xslt_path = determine_document_type(xml_path)
    if not doc_type:
        console.print(
            "Could not determine if document is eICR or RR. Validation aborted.",
            style="bold bright_red",
        )
        return

    console.print(f"Detected document type: {doc_type.upper()}", style="bold blue")

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
