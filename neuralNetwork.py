import uproot
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Dense
from selectionPlots import findAllFilesInPath

# Get the samples from the outputNTuples folder, store them in a dictionary with 1 for signal and 0 for background
sampleNames = findAllFilesInPath("*.root", "outputNTuples/")
nTupleSamples = dict.fromkeys(sampleNames, 0)
nTupleSamples["ZHlltt"] = 1
nTupleSamples["ggZH"] = 1

# Tuple of variables to get from each file
variables = ["tauPtSum", "zMassSum", "metPt", "deltaRll", "deltaRtt", "deltaEtall", "deltaEtatt", "nJets",
             "deltaPhill", "deltaPhitt", "deltaPhilltt", "mmc"]

for cut in ["2lep", "3lep"]: # Loop over the different selection cuts (2 and 3 lepton)
  X = np.array([])
  y = np.array([])

  for sample in nTupleSamples: # Loop over the samples
    tree = uproot.open(sample + ":nominal" + cut)
    tree.show()

    # Properties
    XTemp = tree.arrays(["tauPtSum", "zMassSum", "metPt", "deltaRll", "deltaRtt", "deltaEtall", "deltaEtatt", "nJets",
             "deltaPhill", "deltaPhitt", "deltaPhilltt", "mmc"], library = "pd")

    weight = tree.arrays(["weight"], library = "pd")


    # 1 for signal, 0 for background
    yTemp = np.zeros(len(XTemp)) if nTupleSamples[sample] == 0 else np.ones(len(XTemp))

    # Concatenate the arrays
    X = np.concatenate((X, XTemp))
    y = np.concatenate((y, yTemp))

  # Scale the data
  sc = StandardScaler()
  X = sc.fit_transform(X)

  # One hot encode the labels
  ohe = OneHotEncoder()
  y = ohe.fit_transform(y).toarray()

  # Split the data into training and testing sets
  X_train,X_test,y_train,y_test = train_test_split(X,y,test_size = 0.1)

  # Create the model
  model = Sequential()
  model.add(Dense(10, input_dim = 12, activation = "relu")) # Hidden layer with 10 nodes
  model.add(Dense(6, activation = "relu")) # Hidden layer with 6 nodes
  model.add(Dense(2, activation = "softmax")) # 2 output nodes for 2 classes
  model.compile(loss = "categorical_crossentropy", optimizer = "adam", metrics = ["accuracy"]) # Compile the model
