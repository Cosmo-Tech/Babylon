import pandas as pd


def dataframe_to_dict(df: pd.DataFrame, input_types: dict) -> list:
    """
    Convert a pandas DataFrame to a list of dictionaries.

    Args:
      df (pandas.DataFrame): The DataFrame to convert.
      input_types (dict): A dictionary mapping parameter names to their types.

    Returns:
      list: A list of dictionaries to be used with the cosmotech-api
    """
    result = []
    for line in df.itertuples():
        d = dict()
        d['organizationId'] = line.organizationId
        d['workspaceId'] = line.workspaceId
        d['id'] = line.id
        d['name'] = line.name
        d['description'] = line.description
        d['runTemplateId'] = line.runTemplateId
        if line.scenarioId:
            d['scenarioId'] = line.scenarioId
        if line.scenariorunId:
            d['scenariorunId'] = line.scenariorunId
        d['parameterValues'] = []
        for parameter_value in input_types:
            d['parameterValues'].append({
                'parameterId': parameter_value,
                'value': getattr(line, parameter_value),
                'varType': input_types[parameter_value]
            })
        result.append(d)
    return result
