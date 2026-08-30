from agents.gemini_extraction_agent import extract_evidence


transcript = """
My name is Almaz Wolde. I have a spice mill in Bekoji Tera.
We have eight employees, six of them are women.
We produce and package berbere and sell it to shops in
Bekoji and another town.

I want support to expand the business and increase our
production capacity.

I don't remember our exact sales figures right now.
"""


result = extract_evidence(transcript)

print(result)