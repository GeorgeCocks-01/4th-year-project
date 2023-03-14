import shap
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

matplotlib.use("SVG") # Use SVG for matplotlib

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']
plt.rcParams.update({'font.size': 30})

legend_font_size = 28

def predictionsROCPlotter(model, pred, y_test, y_train, X_train, cut, filename = None):
  ### Plots Predictions and ROC curve ###
  fpr, tpr, thresholds = roc_curve(y_test, pred) # Calculate the ROC curve
  rocArea = auc(fpr, tpr) # Calculate the area under the ROC curve

  # Plot the ROC curve
  plt.figure(figsize = (10, 9))
  plt.plot([0, 1], [0, 1], linestyle = "--", color = "black")
  plt.plot(fpr, tpr)
  # plt.title(cut + " ROC curve")
  plt.ylabel("True positive rate")
  plt.xlabel("False positive rate")
  plt.legend(["Baseline", "ROC curve (area = %0.3f)" % rocArea], loc = 'lower right', fontsize = legend_font_size)
  if not filename:
    plt.savefig("nnPlots/roc" + cut + ".png")
  else:
    plt.savefig(filename.split("/")[0] + "/roc" + filename.split("/")[1])
  plt.clf()

  signalPredictionTest = pred[y_test == 1]
  backgroundPredictionTest = pred[y_test == 0]
  # verbose = 0 means no output
  signalPredictionTrain = model.predict(X_train, verbose = 0)[y_train == 1]
  backgroundPredictionTrain = model.predict(X_train, verbose = 0)[y_train == 0]

  # Plot the predictions
  plt.figure(figsize = (10, 9))
  for i, j in zip((signalPredictionTest, backgroundPredictionTest, signalPredictionTrain, backgroundPredictionTrain),
    ("Signal Test", "Background Test", "Signal Train", "Background Train")):
    counts, bins = np.histogram(i, bins = 50, range = (0, 1))
    plt.hist(i, bins = 50, range = (0, 1), label = j, histtype= "step", density = True)
    bin_centres = 0.5*(bins[1:] + bins[:-1])
    errors = np.sqrt(counts)/(len(i)*np.diff(bins))
    counts_density = counts/(len(i)*np.diff(bins))
    plt.errorbar(bin_centres, counts_density, yerr = errors, ls = "none", capsize = 2)

  # plt.title(cut + " Prediction (testing)")
  plt.ylabel("Normalised number of events")
  plt.xlabel("Prediction")
  plt.legend(loc = 'upper center', fontsize = legend_font_size)
  if not filename:
    plt.savefig("nnPlots/predictions" + cut + ".png")
  else:
    plt.savefig(filename.split("/")[0] + "/predictions" + filename.split("/")[1])
  plt.clf()

def trainingPlotter(modelFit, cut):
  ### Plots the loss and accuracy for each epoch of training ###
  for i in ("loss", "accuracy"):
    plt.figure(figsize = (10, 9))
    plt.plot(modelFit.history[i])
    plt.plot(modelFit.history["val_" + i])
    plt.title(cut + " Model" + i.capitalize())
    plt.ylabel(i.capitalize())
    plt.xlabel("Epoch")
    plt.legend(['Train', 'Test'], loc = 'upper left')
    plt.savefig("nnPlots/" + i + cut + ".png")
    plt.clf()

def shapPlotter(model, X_train, cut):
  ### Plots the SHAP values ###

  # Tuple of variables to get from each file
  variables = ("tauPtSum", "zMassSum", "metPt", "deltaRll", "deltaRtt", "deltaRttll", "deltaEtall", "deltaEtatt",
              "nJets", "deltaPhill", "deltaPhitt", "deltaPhilltt", "mmc")

  explainer = shap.Explainer(model, X_train, feature_names = variables)
  shap_values = explainer(X_train)

  shap.plots.bar(shap_values, show = False)
  plt.gcf().set_size_inches(8, 5)

  # ax_list = shap_fig.axes
  # ax_list[0].set_xlabel(fontsize = 20)
  # ax_list[0].set_ylabel(fontsize = 20)

  plt.savefig("nnPlots/shapBar" + cut + ".png")
  plt.clf()
