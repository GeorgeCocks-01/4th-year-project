import argparse
import numpy as np
from keras.models import load_model
from selectionPlots import findAllFilesInPath
from nnTrain import getSplitData
from sklearn.metrics import accuracy_score
from plotting import predictionsROCPlotter, shapPlotter

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

    # Load the model
    if args.inputModel:
      model = load_model("nnModels/" + args.inputModel + ".h5")
    else:
      model = load_model("nnModels/nnModel" + cut + ".h5")

    # Predict the labels
    pred = model.predict(X_test)
    y_pred = np.rint(pred).astype(int)

    # Get the accuracy
    print("Accuracy for " + cut + " cut: " + str(accuracy_score(y_test, y_pred)))

    # Plot graphs
    predictionsROCPlotter(model, pred, y_test, y_train, X_train, cut)

    if args.shap:
      # Plot the SHAP values
      shapPlotter(model, X_train, variables, cut)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description = "Predict and plot graphs using an imported neural network")
  parser.add_argument("-i", "--input", type = str, dest = "inputModel", default = None,
    help = "Input file name of the neural network model.")
  parser.add_argument("-s", "--SHAP", action = "store_true", dest = "shap", default = None,
    help = "Whether to plot the SHAP values or not.")
  args = parser.parse_args()

  main(args)
