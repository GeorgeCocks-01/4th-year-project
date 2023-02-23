import uproot
import argparse
import numpy as np
from keras.optimizers import Adam
from keras.layers import Dense
from keras.models import Sequential
from keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from selectionPlots import findAllFilesInPath
from plotting import predictionsROCPlotter, trainingPlotter

def getSplitData(cut, seed):
  # Get the samples from the outputNTuples folder, store them in a dictionary with 1 for signal and 0 for background
  sampleNames = findAllFilesInPath("*.root", "nTupleGroups/")
  nTupleSamples = dict.fromkeys(sampleNames, 0)
  nTupleSamples["nTupleGroups/signalGroup.root"] = 1

  # Tuple of variables to get from each file
  variables = ("tauPtSum", "zMassSum", "metPt", "deltaRll", "deltaRtt", "deltaRttll", "deltaEtall", "deltaEtatt",
               "nJets", "deltaPhill", "deltaPhitt", "deltaPhilltt", "mmc")

  x = np.array([])
  y = np.array([])

  for sample in nTupleSamples: # Loop over the samples

    with uproot.open(sample + ":nominal" + cut) as tree:
      x_temp = tree.arrays(variables, library = "pd")
      weight = tree["weight"].array(library = "np")

    x_temp = x_temp.iloc[:, :].values

    # 1 for signal, 0 for background
    y_temp = np.zeros(len(x_temp)) if nTupleSamples[sample] == 0 else np.ones(len(x_temp))

    # Concatenate the arrays
    x = np.concatenate((x, x_temp)) if x.size else x_temp
    y = np.concatenate((y, y_temp)) if y.size else y_temp

  # Scale the data
  sc = StandardScaler()
  x = sc.fit_transform(x)

  # Split the data into training and testing sets. random_state is the seed for the random number generator
  x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.2, random_state = seed)

  return x_train, x_test, y_train, y_test

def main(args):
  for cut in ["2lep", "3lep"]: # Loop over the different selection cuts (2 and 3 lepton)

    x_train, x_test, y_train, y_test = getSplitData(cut, 0)

    # Create the model
    model = Sequential()
    model.add(Dense(30, input_dim = 13, activation = "relu")) # Hidden layer
    model.add(Dense(18, activation = "relu")) # Hidden layer
    model.add(Dense(16, activation = "relu")) # Hidden layer
    # model.add(Dense(18, activation = "relu")) # Hidden layer
    model.add(Dense(1, activation = "sigmoid")) # Only need one output node for binary classification
    # opt = Adam(learning_rate = 0.001643) # adam uses a learning rate of 0.001 by default
    model.compile(loss = "binary_crossentropy", optimizer = "adam", metrics = ["accuracy"]) # Compile the model

    # Create an early stopping callback
    stop_early = EarlyStopping(monitor = "val_loss", patience = 5, restore_best_weights = True, verbose = 1)

    # Train the model
    model_fit = model.fit(x_train, y_train, validation_data = (x_test, y_test), epochs=50, batch_size=64,
                         callbacks=[stop_early])

    # Save the model
    if args.outputfile:
      model.save("nnModels/" + args.outputfile + ".h5")
    else:
      model.save("nnModels/trained" + cut + ".h5")

    # Predict the labels
    pred = model.predict(x_test)

    # Plot graphs
    trainingPlotter(model_fit, cut)
    predictionsROCPlotter(model, pred, y_test, y_train, x_train, cut)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description = "Train a neural network on the nTuples.")
  parser.add_argument("-o", "--output", metavar = "OUTPUT", type = str, dest = "outputfile", default = None,
                      help = "Ouptut file name for the model to be saved into.")
  args = parser.parse_args()

  main(args)
