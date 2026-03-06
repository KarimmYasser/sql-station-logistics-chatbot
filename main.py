"""
CLI entry-point for the logistics assistant.
Launches an interactive prompt loop that feeds user
queries into the LangGraph pipeline and prints results.
"""

from agent.graph import app


def run_interactive_session():
    """Start the read-eval-print loop for the logistics assistant."""
    banner = (
        "========================================\n"
        "  Space Station Logistics AI  (CLI)     \n"
        "  Type 'exit' or 'quit' to disconnect.  \n"
        "========================================"
    )
    print(banner + "\n")

    while True:
        try:
            raw_input_text = input("Captain: ").strip()

            if len(raw_input_text) == 0:
                continue

            if raw_input_text.lower() in ('exit', 'quit'):
                print("Station AI: Comm channel closed. Goodbye.")
                break

            pipeline_input = {"question": raw_input_text}
            run_config = {"configurable": {"thread_id": "cli_captain"}}

            output = app.invoke(pipeline_input, config=run_config)

            if output.get('messages') and len(output['messages']) > 0:
                answer_text = output['messages'][-1].content
                print(f"\nStation AI: {answer_text}\n")
            else:
                print("\nStation AI: Unrecognized syntax. Unable to process.\n")

        except KeyboardInterrupt:
            print("\nStation AI: Comm channel closed. Goodbye.")
            break
        except Exception as err:
            print(f"\nSystem Error: {err}\n")


if __name__ == "__main__":
    run_interactive_session()
