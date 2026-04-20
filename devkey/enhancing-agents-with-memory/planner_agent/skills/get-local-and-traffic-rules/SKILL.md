---
name: get-local-and-traffic-rules
description: Retrieve local rules and traffic information for a specific jurisdiction.
---
# get_local_and_traffic_rules Skill

This skill provides guidelines on how to effectively use the `get_local_and_traffic_rules` tool.

## Overview
The `get_local_and_traffic_rules` tool interfaces with an AlloyDB database to perform vector similarity searches on a corpus of rules and traffic information using a provided natural language query.

## Usage Guidelines
1. **Query Specificity**: When calling the tool, provide specific details in the `query` argument. For example, instead of querying "food rules", use "rules regarding food vendors during public events".
2. **Contextual Use**: Use the tool when planning events or activities that require adherence to local municipal or state rules (e.g., street closures, noise ordinances, environmental rules).
3. **Handling Results**: The tool returns a string containing the text of the top 5 most relevant rules. If no error occurs, parse the returned string to inform your planning tasks.
4. **Error Handling**: If an error string is returned (e.g., "Error querying rules: ..."), you must report this failure or attempt an alternative approach if applicable.

## Underlying Mechanism
- The tool uses `google_ml.embedding` to convert the query into a vector representation.
- It calculates distance (`<=>`) against the `embedding` column in the `rules` table on an AlloyDB instance.
- Results are fetched in descending order of similarity, limited to 5 results.