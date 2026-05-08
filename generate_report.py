from reports.report_generator import create_pdf_report


def main():
    output_path = create_pdf_report()
    print(f"PDF report generated: {output_path}")


if __name__ == "__main__":
    main()