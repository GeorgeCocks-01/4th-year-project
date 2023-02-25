import array
import ROOT
import uproot
import argparse
import numpy as np
from math import sqrt
from keras.models import load_model
from sklearn.metrics import accuracy_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from selectionPlots import findAllFilesInPath
from plotting import predictionsROCPlotter

def main(args):
  # Get the samples from the outputNTuples folder, store them in a dictionary with 1 for signal and 0 for background
  sample_names = findAllFilesInPath("*.root", "nTupleGroups/")
  ntuple_samples = dict.fromkeys(sample_names, 0)
  ntuple_samples["nTupleGroups/signalGroup.root"] = 1

  # Tuple of variables to get from each file
  variables = ("tauPtSum", "zMassSum", "metPt", "deltaRll", "deltaRtt", "deltaRttll", "deltaEtall", "deltaEtatt",
              "nJets", "deltaPhill", "deltaPhitt", "deltaPhilltt", "mmc")

  # Create a canvas
  ROOT.gROOT.LoadMacro('../atlasrootstyle/AtlasStyle.C')
  ROOT.gROOT.LoadMacro('../atlasrootstyle/AtlasUtils.C')
  ROOT.gROOT.SetBatch(ROOT.kTRUE)
  ROOT.SetAtlasStyle()
  canvas = ROOT.TCanvas("c", "c", 800, 600)
  canvas.cd()

  for cut in ["2lep", "3lep"]: # Loop over the different selection cuts (2 and 3 lepton)
    batch = 64 if cut == "2lep" else 128

    ### GET THE DATA ###
    x = np.array([])
    y = np.array([])
    weight = np.array([])

    for sample in ntuple_samples: # Loop over the samples

      with uproot.open(sample + ":nominal" + cut) as tree:
        x_temp = tree.arrays(variables, library = "pd")
        weight_temp = tree["weight"].array(library = "np")

      x_temp = x_temp.iloc[:, :].values

      # 1 for signal, 0 for background
      yTemp = np.zeros(len(x_temp)) if ntuple_samples[sample] == 0 else np.ones(len(x_temp))

      # Concatenate the arrays
      x = np.concatenate((x, x_temp)) if x.size else x_temp
      y = np.concatenate((y, yTemp)) if y.size else yTemp
      weight = np.concatenate((weight, weight_temp)) if weight.size else weight_temp

    # Scale the data
    sc = StandardScaler()
    x = sc.fit_transform(x)
    ### ###

    # Create a kFold object
    kf = KFold(n_splits = 5, shuffle = True, random_state = 0)

    # Create a ROOT histogram for the predictions and fill it
    signal_predictions = ROOT.TH1D("Signalpredictions" + cut, "Predictions " + cut + " " + ";Prediction;Events", 25, 0, 1)
    background_predictions = ROOT.TH1D("Backgroundpredictions" + cut, "Predictions " + cut + " " + ";Prediction;Events", 25, 0, 1)

    i = 1
    # Loop over the kFold splits
    for train, test in kf.split(x):
      model = load_model("nnModels/architechture" + cut + ".h5")

      x_train, x_test = x[train], x[test]
      y_train, y_test = y[train], y[test]
      weights_test = weight[test]

      print("Starting fold", i, "for", cut, "cut")
      # Fit the model
      model.fit(x_train, y_train, batch_size = batch, epochs = 10, verbose = 0)

      # Get the predictions
      pred = model.predict(x_test)
      # Round the predictions to the nearest integer
      y_pred = np.rint(pred).astype(int)
      # Get the accuracy
      print("Accuracy for fold", i, ": ", accuracy_score(y_test, y_pred))

      # Save the model
      if args.outputfile:
        model.save("kFoldModels/" + args.outputfile + cut + str(i) + ".h5")
      else:
        model.save("kFoldModels/" + cut + "Model" + str(i) + ".h5")

      # Plot the ROC curve
      predictionsROCPlotter(model, pred, y_test, y_train, x_train, cut, "kFoldPlots/" + cut + str(i) + ".png")

      # for j in pred: WOULD NEED TO BE CHANGED
      #   signal_predictions.Fill(j, weights_test[j])
      #   background_predictions.Fill(j, weights_test[j])

      # Arrays of predictions for signal and background
      pred_signal = array.array('d', pred[y_test == 1])
      pred_background = array.array('d', pred[y_test == 0])
      # Arrays of weights for signal and background
      weights_signal = array.array('d', weights_test[y_test == 1])
      weights_background = array.array('d', weights_test[y_test == 0])

      # Fill the histogram (must use python arrays)
      signal_predictions.FillN(len(pred_signal), pred_signal, weights_signal)
      background_predictions.FillN(len(pred_background), pred_background, weights_background)

      i += 1

    # # Save the histogram to a ROOT file
    # root_file = ROOT.TFile.Open("kFoldRoot/prediction" + cut + ".root", "RECREATE")
    # root_file.cd()
    # signal_predictions.Write()
    # root_file.Close()

    ### PLOTTING ###
    # Create a legend
    leg = ROOT.TLegend(0.7,0.6,0.8,0.85)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.03)
    leg.SetEntrySeparation(0.001)

    histos = [signal_predictions, background_predictions]
    colours = [ROOT.kRed, ROOT.kBlue]
    sample_name = ["Signal", "Background"]
    prediction_yield = 0
    for i in range(len(histos)):
      prediction_yield += histos[i].Integral(0, histos[i].GetNbinsX() + 1)
      histos[i].SetLineColor(colours[i])

      # Normalise the histograms
      histos[i].Scale(1./histos[i].Integral())

    if histos[0].GetMaximum() > histos[1].GetMaximum():
      maximum = histos[0].GetMaximum()
    else:
      maximum = histos[1].GetMaximum()

    for i in range(len(histos)):
      histos[i].SetMaximum(maximum * 1.3)

      # Draw the histograms
      histos[i].Draw("hist") if i == 0 else histos[i].Draw("histSAME")

      leg.AddEntry(histos[i], sample_name[i], "l")

    leg.Draw('SAME')

    # Save the canvas
    canvas.SaveAs("kFoldPlots/weightedPrediction" + cut + ".pdf")
    canvas.Clear()
    ### END OF PLOTTING ###

    ### SB ratio histograms ###
    sb_1 = signal_predictions.Clone("SBsignal1" + cut)
    sb_2 = signal_predictions.Clone("SBsignal2" + cut)

    for i in range(1, signal_predictions.GetNbinsX() + 1):
      # Calculate the S/sqrt(S+B) up to bin i
      signal_yield = signal_predictions.Integral(0, i)
      background_yield = background_predictions.Integral(0, i)
      try:
        SoverSqrtSB = signal_yield/sqrt(signal_yield + background_yield)
      except ZeroDivisionError:
        SoverSqrtSB = 0
      except ValueError:
        SoverSqrtSB = 0
      sb_1.SetBinContent(i, SoverSqrtSB)

      # Calculate the S/sqrt(S+B) from bin i to the end
      signal_yield = signal_predictions.Integral(i, signal_predictions.GetNbinsX() + 1)
      background_yield = background_predictions.Integral(i, background_predictions.GetNbinsX() + 1)
      try:
        SoverSqrtSB = signal_yield/sqrt(signal_yield + background_yield)
      except ZeroDivisionError:
        SoverSqrtSB = 0
      except ValueError:
        SoverSqrtSB = 0
      sb_2.SetBinContent(i, SoverSqrtSB)

    sb_1.SetMaximum(sb_1.GetMaximum()*3.5)
    sb_1.SetLineWidth(3)
    sb_1.SetMarkerColor(ROOT.kRed)
    sb_1.SetLineColor(ROOT.kRed)
    sb_1.Draw('hist')
    sb_1.GetYaxis().SetTitle("S/sqrt(S+B)")

    sb_2.SetMaximum(sb_2.GetMaximum()*5)
    sb_2.SetMarkerColor(ROOT.kBlue)
    sb_2.SetLineColor(ROOT.kBlue)
    sb_2.Draw('histSAME')
    canvas.SaveAs("kFoldPlots/SoverSqrtSB" + cut + ".pdf")
    canvas.Clear()
    ### End of SB ratio histograms ###

    # print("Yield for cut", cut, "is", prediction_yield)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description = "Train a neural network on the nTuples.")
  parser.add_argument("-o", "--output", metavar = "OUTPUT", type = str, dest = "outputfile", default = None,
                      help = "Ouptut file name for the model to be saved into.")
  args = parser.parse_args()

  main(args)
