from pyannote.audio import Pipeline

def get_pipeline(pipeline_name, use_auth_token):
    return Pipeline.from_pretrained(pipeline_name, use_auth_token=use_auth_token)