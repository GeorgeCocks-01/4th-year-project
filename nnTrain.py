import uproot
import argparse
import numpy as np
from keras.layers import Dense
from keras.models import Sequential
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from selectionPlots import findAllFilesInPath
from plotting import predictionsROCPlotter, trainingPlotter

def getSplitData(nTupleSamples, variables, cut, seed):
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

  # Split the data into training and testing sets. random_state is the seed for the random number generator
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = seed)

  return X_train, X_test, y_train, y_test


def main(args):
  # Get the samples from the outputNTuples folder, store them in a dictionary with 1 for signal and 0 for background
  sampleNames = findAllFilesInPath("*.root", "nTupleGroups/")
  nTupleSamples = dict.fromkeys(sampleNames, 0)
  nTupleSamples["nTupleGroups/signalGroup.root"] = 1

  # Tuple of variables to get from each file
  variables = ("tauPtSum", "zMassSum", "metPt", "deltaRll", "deltaRtt", "deltaRttll", "deltaEtall", "deltaEtatt",
              "nJets", "deltaPhill", "deltaPhitt", "deltaPhilltt", "mmc")

  for cut in ["2lep", "3lep"]: # Loop over the different selection cuts (2 and 3 lepton)

    X_train, X_test, y_train, y_test = getSplitData(nTupleSamples, variables, cut, 0)

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
    if args.outputfile:
      model.save("nnModels/" + args.outputfile + ".h5")
    else:
      model.save("nnModels/nnModel" + cut + ".h5")

    # Predict the labels
    pred = model.predict(X_test)

    # Plot graphs
    trainingPlotter(modelFit, cut)
    predictionsROCPlotter(model, pred, y_test, y_train, X_train, cut)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description = "Train a neural network on the nTuples.")
  parser.add_argument("-o", "--output", metavar = "OUTPUT", type = str, dest = "outputfile", default = None,
    help = "Ouptut file name for the model to be saved into.")
  args = parser.parse_args()

  main(args)
