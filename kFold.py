import uproot
import argparse
import numpy as np
from keras.models import load_model
from keras.callbacks import EarlyStopping
from sklearn.metrics import accuracy_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from selectionPlots import findAllFilesInPath
from plotting import predictionsROCPlotter

def main(args):
  # Get the samples from the outputNTuples folder, store them in a dictionary with 1 for signal and 0 for background
  sampleNames = findAllFilesInPath("*.root", "nTupleGroups/")
  nTupleSamples = dict.fromkeys(sampleNames, 0)
  nTupleSamples["nTupleGroups/signalGroup.root"] = 1

  # Tuple of variables to get from each file
  variables = ("tauPtSum", "zMassSum", "metPt", "deltaRll", "deltaRtt", "deltaRttll", "deltaEtall", "deltaEtatt",
              "nJets", "deltaPhill", "deltaPhitt", "deltaPhilltt", "mmc")

  for cut in ["2lep", "3lep"]: # Loop over the different selection cuts (2 and 3 lepton)
    batch = 64 if cut == "2lep" else 128

    ### GET THE DATA ###
    x = np.array([])
    y = np.array([])

    for sample in nTupleSamples: # Loop over the samples

      with uproot.open(sample + ":nominal" + cut) as tree:
        XTemp = tree.arrays(variables, library = "pd")
        weight = tree["weight"].array(library = "np")

      XTemp = XTemp.iloc[:, :].values

      # 1 for signal, 0 for background
      yTemp = np.zeros(len(XTemp)) if nTupleSamples[sample] == 0 else np.ones(len(XTemp))

      # Concatenate the arrays
      x = np.concatenate((x, XTemp)) if x.size else XTemp
      y = np.concatenate((y, yTemp)) if y.size else yTemp

    # Scale the data
    sc = StandardScaler()
    x = sc.fit_transform(x)
    ### ###

    # Create an early stopping callback
    stop_early = EarlyStopping(monitor = "val_loss", patience = 5, restore_best_weights = True, verbose = 1)

    # Create a kFold object
    kf = KFold(n_splits = 5, shuffle = True, random_state = 0)

    i = 1
    # Loop over the kFold splits
    for train, test in kf.split(x):

      model = load_model("nnModels/architechture" + cut + ".h5")

      x_train, x_test = x[train], x[test]
      y_train, y_test = y[train], y[test]

      # Fit the model
      model.fit(x_train, y_train, batch_size = batch, epochs = 100, callbacks = [stop_early])

      # Get the predictions
      pred = model.predict(x_test)
      # Get the accuracy
      print("Accuracy for fold" + i + ": " + str(accuracy_score(y_test, pred)))

      # Save the model
      if args.outputfile:
        model.save("kFoldModels/" + args.outputfile + cut + i + ".h5")
      else:
        model.save("kFoldModels/" + cut + "Model" + i + ".h5")

      # Plot the ROC curve
      predictionsROCPlotter(model, pred, y_test, y_train, x_train, cut, "kFoldModels/" + cut + i + ".png")

      i += 1

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description = "Train a neural network on the nTuples.")
  parser.add_argument("-o", "--output", metavar = "OUTPUT", type = str, dest = "outputfile", default = None,
                      help = "Ouptut file name for the model to be saved into.")
  args = parser.parse_args()

  main(args)
