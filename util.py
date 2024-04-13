import pickle


def load_model():
    with open('artefacts/model.pkl', 'rb') as f:
        model = pickle.load(f)
    return model

def load_data():
    with open('artefacts/df.pkl', 'rb') as f:
        df = pickle.load(f)
    return df

def load_model_car():
    with open('artefacts/models.pkl', 'rb') as f:
        model = pickle.load(f)
    return model

# def load_model2():
  #  with open('model2.pkl', 'rb') as f:
  #      model2 = pickle.load(f)
  #  return model2

# and so on for all your models
