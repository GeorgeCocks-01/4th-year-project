import uproot
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from selectionPlots import findAllFilesInPath
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics import roc_curve
from sklearn.metrics import auc
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

  # Split the data into training and testing sets
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2)

  # Create the model
  model = Sequential()
  model.add(Dense(15, input_dim = 13, activation = "relu")) # Hidden layer
  model.add(Dense(11, activation = "relu")) # Hidden layer
  model.add(Dense(8, activation = "relu")) # Hidden layer
  model.add(Dense(1, activation = "sigmoid")) # Only need one output node for binary classification
  model.compile(loss = "binary_crossentropy", optimizer = "adam", metrics = ["accuracy"]) # Compile the model
  # adam uses a learning rate of 0.001 by default

  # Train the model
  modelFit = model.fit(X_train, y_train, validation_data = (X_test, y_test), epochs=50, batch_size=64)

  # Save the model
  model.save("nnModels/nnModel" + cut + ".h5")

  # Predict the labels
  y_pred = model.predict(X_test)
  pred = np.rint(y_pred).astype(int)

  fpr, tpr, thresholds = roc_curve(y_test, y_pred) # Calculate the ROC curve
  rocArea = auc(fpr, tpr) # Calculate the area under the ROC curve

  # Plot the ROC curve
  plt.figure(figsize=(8, 6))
  plt.plot([0, 1], [0, 1], linestyle = "--", color = "black")
  plt.plot(fpr, tpr)
  plt.title(cut + " ROC curve")
  plt.ylabel("True positive rate")
  plt.xlabel("False positive rate")
  plt.legend(["Baseline", "ROC curve (area = %0.3f)" % rocArea], loc = 'lower right')
  plt.savefig("nnPlots/nnROC" + cut + ".png")
  plt.clf()

  # Calculate the accuracy
  accuracy = accuracy_score(y_test, pred)
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

  signalPredictionTest = y_pred[y_test == 1]
  backgroundPredictionTest = y_pred[y_test == 0]

  plt.figure(figsize=(8, 6))
  plt.hist(signalPredictionTest, bins = 50, range = (0, 1), label = "Signal", alpha = 0.5)
  plt.hist(backgroundPredictionTest, bins = 50, range = (0, 1), label = "Background", alpha = 0.5)
  plt.title(cut + " Prediction (testing)")
  plt.ylabel("Number of events")
  plt.xlabel("Prediction")
  plt.legend(loc = 'upper left')
  plt.savefig("nnPlots/nnTest" + cut + ".png")
  plt.clf()

  signalPredictionTrain = model.predict(X_train)[y_train == 1]
  backgroundPredictionTrain = model.predict(X_train)[y_train == 0]

  plt.figure(figsize=(8, 6))
  plt.hist(signalPredictionTrain, bins = 50, range = (0, 1), label = "Signal", alpha = 0.5)
  plt.hist(backgroundPredictionTrain, bins = 50, range = (0, 1), label = "Background", alpha = 0.5)
  plt.title(cut + " Prediction (training)")
  plt.ylabel("Number of events")
  plt.xlabel("Prediction")
  plt.legend(loc = 'upper left')
  plt.savefig("nnPlots/nnTrain" + cut + ".png")
  plt.clf()
