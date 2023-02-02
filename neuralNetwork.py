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

  # One-hot-encode the labels
  ohe = OneHotEncoder()
  y = ohe.fit_transform(y.reshape(-1,1)).toarray()

  # Split the data into training and testing sets
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2)

  # Create the model
  model = Sequential()
  model.add(Dense(15, input_dim = 13, activation = "relu")) # Hidden layer
  model.add(Dense(11, activation = "relu")) # Hidden layer
  model.add(Dense(8, activation = "relu")) # Hidden layer
  model.add(Dense(2, activation = "sigmoid")) # 2 output nodes for 2 classes
  model.compile(loss = "binary_crossentropy", optimizer = "adam", metrics = ["accuracy"]) # Compile the model
  # adam uses a learning rate of 0.001 by default

  # Train the model
  modelFit = model.fit(X_train, y_train, validation_data = (X_test, y_test), epochs=50, batch_size=64)

  # Predict the labels
  y_pred = model.predict(X_test)
  pred = list(np.argmax(y_pred, axis = 1))
  test = list(np.argmax(y_test, axis = 1)) # Inverse one-hot-encoding the labels

  # Calculate the accuracy
  accuracy = accuracy_score(test, pred)
  print("Accuracy is:", accuracy*100, "% on the test set.")

  # Plot the loss and accuracy
  plt.figure(figsize=(8, 6))
  plt.plot(modelFit.history["loss"])
  plt.plot(modelFit.history["val_loss"])
  plt.title(cut + " Model loss")
  plt.ylabel("Loss")
  plt.xlabel("Epoch")
  plt.legend(['Train', 'Test'], loc = 'upper left')
  plt.savefig("nnPlots/nnLoss" + cut + ".png")
  plt.clf()

  plt.figure(figsize=(8, 6))
  plt.plot(modelFit.history["accuracy"])
  plt.plot(modelFit.history["val_accuracy"])
  plt.title(cut + " Model accuracy")
  plt.ylabel("Accuracy")
  plt.xlabel("Epoch")
  plt.legend(['Train', 'Test'], loc = 'upper left')
  plt.savefig("nnPlots/nnAccuracy" + cut + ".png")
  plt.clf()
