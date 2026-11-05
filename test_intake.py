"""Manual extraction smoke test.

Run this file directly with a configured ``GEMINI_API_KEY``. It is not part
of the automated test suite because it calls the external model provider.
"""


def main() -> None:
    from agents.ai_agents import extract_evidence

    transcript = """
    My name is Almaz Wolde. I have a spice mill in Bekoji Tera.
    We have eight employees, six of them are women.
    We produce and package berbere and sell it to shops in
    Bekoji and another town.

    I want support to expand the business and increase our
    production capacity.

    I don't remember our exact sales figures right now.
    """

    print(extract_evidence(transcript))


if __name__ == "__main__":
    main()