import uproot
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from selectionPlots import findAllFilesInPath
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from keras.models import Sequential
from keras.layers import Dense
from keras.models import load_model

matplotlib.use("SVG") # Use SVG for matplotlib

# Get the samples from the outputNTuples folder, store them in a dictionary with 1 for signal and 0 for background
sampleNames = findAllFilesInPath("*.root", "nTupleGroups/")
nTupleSamples = dict.fromkeys(sampleNames, 0)
nTupleSamples["nTupleGroups/signalGroup.root"] = 1

# Tuple of variables to get from each file
variables = ["tauPtSum", "zMassSum", "metPt", "deltaRll", "deltaRtt", "deltaRttll", "deltaEtall", "deltaEtatt",
             "nJets", "deltaPhill", "deltaPhitt", "deltaPhilltt", "mmc"]

for cut in ["2lep", "3lep"]: # Loop over the different selection cuts (2 and 3 lepton)
  X = np.array([])
  y = np.array([])

  for sample in nTupleSamples: # Loop over the samples

    with uproot.open(sample + ":nominal" + cut) as tree:
      XTemp = tree.arrays(variables, library = "pd")
      weight = tree["weight"].array(library = "np")

    XTemp = XTemp.iloc[:, :].values

    # 1 for signal, 0 for background
    yTemp = np.zeros(len(XTemp)) if nTupleSamples[sample] == 0 else np.ones(len(XTemp))

    # Concatenate the arrays
    X = np.concatenate((X, XTemp)) if X.size else XTemp
    y = np.concatenate((y, yTemp)) if y.size else yTemp

  # Scale the data
  sc = StandardScaler()
  X = sc.fit_transform(X)

  # Load the model
  model = load_model("nnModels/nnModel" + cut + ".h5")

  # Predict the labels
  y_pred = model.predict(X)
  y_pred = np.argmax(y_pred, axis = 1)

  # Get the accuracy
  print("Accuracy for " + cut + " cut: " + str(accuracy_score(y, y_pred)))
