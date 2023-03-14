from array import array
import uproot
import ctypes
import ROOT
import numpy as np
from selectionPlots import findAllFilesInPath

def significance_calc(bin, signal_hist, background_hist):
  signal_yield = signal_hist.GetBinContent(bin)
  background_yield = background_hist.GetBinContent(bin)
  try:
    sb = signal_yield/np.sqrt(signal_yield + background_yield)
  except RuntimeWarning:
    sb = 0
  return sb

def main():
  # Create a canvas
  ROOT.gROOT.LoadMacro('../atlasrootstyle/AtlasStyle.C')
  ROOT.gROOT.LoadMacro('../atlasrootstyle/AtlasUtils.C')
  ROOT.gROOT.SetBatch(ROOT.kTRUE)
  ROOT.SetAtlasStyle()
  canvas = ROOT.TCanvas("c", "c", 800, 600)
  canvas.cd()

  # Get the samples from the outputNTuples folder, store them in a dictionary with 1 for signal and 0 for background
  sample_names = findAllFilesInPath("*.root", "nTupleGroups/")

  # Thresholds for 2lep, 3lep cuts
  thresholds = (0.52, 0.15)

  for cut, threshold in zip(("2lep", "3lep"), thresholds):
    # dictionary of the delta phi ll arrays for each sample
    delta_phi_ll_dict = {
      "llll": np.array([]),
      "other di-boson": np.array([]),
      "jets": np.array([]),
      "signal": np.array([])
    }
    weight_dict = dict.fromkeys(delta_phi_ll_dict, np.array([]))
    predictions_dict = dict.fromkeys(delta_phi_ll_dict, np.array([]))

    # Get the delta phi ll arrays for each sample
    for sample in sample_names:
      match sample:
        case "nTupleGroups/signalGroup.root":
          key = "signal"
        case "nTupleGroups/llllGroup.root":
          key = "llll"
        case "nTupleGroups/backgroundGroup.root":
          key = "other di-boson"
        case "nTupleGroups/jetsGroup.root":
          key = "jets"
      with uproot.open(sample + ":nominal" + cut) as tree:
        delta_phi_ll_dict[key] = tree["deltaPhill"].array(library = "np")
        weight_dict[key] = tree["weight"].array(library = "np")

    # Get predictions and group number from kFold.py ntuples
    with uproot.open("kFoldNTuples/predictions.root:nominal" + cut) as f:
      prediction = f["prediction"].array(library = "np")
      group_number = f["group"].array(library = "np")

    # Dictionary of group numbers
    group_dict = {
      "llll": 1,
      "other di-boson": 2,
      "jets": 3,
      "signal": 0
    }

    # Sort predictions into groups
    for key in predictions_dict:
      predictions_dict[key] = prediction[group_number == group_dict[key]]

    # Cut delta phi ll arrays using threshold
    for key in delta_phi_ll_dict:
      delta_phi_ll_dict[key] = delta_phi_ll_dict[key][predictions_dict[key] > threshold]
      weight_dict[key] = weight_dict[key][predictions_dict[key] > threshold]

    # Generate histogram for output
    delta_phi_ll_histograms =  {
      "llll": ROOT.TH1D("llll" + cut, "delta_phi_ll" + cut + ";#Delta #phi_{ll} (Rad);Normalised Counts", 8, -3.14, 3.14),
      "other di-boson": ROOT.TH1D("di-boson" + cut, "delta_phi_ll" + cut + ";#Delta #phi_{ll} (Rad);Normalised Counts", 8, -3.14, 3.14),
      "jets": ROOT.TH1D("jets" + cut, "delta_phi_ll" + cut + ";#Delta #phi_{ll} (Rad);Normalised Counts", 8, -3.14, 3.14),
      "signal": ROOT.TH1D("signal" + cut, "delta_phi_ll" + cut + ";#Delta #phi_{ll} (Rad);Normalised Counts", 8, -3.14, 3.14)
    }

    # Fill histogram with delta phi ll values
    for key in delta_phi_ll_dict:
      arr = array('d', delta_phi_ll_dict[key])
      weight_arr = array('d', weight_dict[key])
      delta_phi_ll_histograms[key].FillN(len(arr), arr, weight_arr)

    # Print yields
    print("Yields for " + cut + " cut")
    background_yield = 0
    error = ctypes.c_double()
    bg_errors = dict.fromkeys(delta_phi_ll_histograms)
    for key in delta_phi_ll_histograms:
      max_bin = delta_phi_ll_histograms[key].GetNbinsX() + 1
      if key == "signal":
        signal_yield = delta_phi_ll_histograms[key].IntegralAndError(0, max_bin, error)
        bg_errors[key] = error.value
        print("Signal yield: ", signal_yield, " +/- ", bg_errors[key])
      else:
        temp_yield = delta_phi_ll_histograms[key].IntegralAndError(0, max_bin, error)
        bg_errors[key] = error.value
        print(key, "yield: ", temp_yield, " +/- ", bg_errors[key])
        background_yield += temp_yield

    backgroundError = np.sqrt(bg_errors["llll"]**2 + bg_errors["other di-boson"]**2 + bg_errors["jets"]**2)

    s_over_b_error = np.sqrt(
      ((signal_yield + bg_errors["signal"])/background_yield
       - signal_yield/background_yield)**2 +
       (signal_yield/(background_yield + backgroundError)
        - signal_yield/background_yield)**2
    )

    significance_error = np.sqrt(
    ((signal_yield + bg_errors["signal"])/np.sqrt(signal_yield + bg_errors["signal"] + background_yield)
     - signal_yield/np.sqrt(signal_yield + background_yield))**2
    + (signal_yield/np.sqrt(signal_yield + background_yield + backgroundError)
       - signal_yield/np.sqrt(signal_yield + background_yield))**2
    )

    print("S/B:", signal_yield/background_yield, " +/- ", s_over_b_error)
    print("S/sqrt(S+B):", signal_yield/np.sqrt(signal_yield + background_yield), " +/- ", significance_error)

    ### PLOTTING ###
    # Create a legend
    leg = ROOT.TLegend(0.5, 0.9, 0.7, 0.75)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.03)
    leg.SetEntrySeparation(0.001)

    colours = [ROOT.kBlack, ROOT.kBlue, ROOT.kGreen, ROOT.kRed]
    maximum = -999
    stacked_hist = ROOT.THStack()
    for i, key in enumerate(delta_phi_ll_histograms):
      hist = delta_phi_ll_histograms[key]
      hist.SetLineColor(colours[i])

      stacked_hist.Add(hist.Clone())

      # Normalise the histograms
      hist.Scale(1./hist.Integral())

      # Get the maximum value of the histograms
      if hist.GetMaximum() > maximum and key != "jets":
        maximum = hist.GetMaximum()

    for i, key in enumerate(delta_phi_ll_histograms):
      hist = delta_phi_ll_histograms[key]
      if i == 0:
        hist.SetMaximum(maximum * 1.2)
        hist.Draw("hist")
      else:
        hist.Draw("histSAME")

      leg.AddEntry(hist, key, "l")

    leg.Draw('SAME')

    # Save the canvas
    canvas.SaveAs("signedDeltaPhill/" + cut + ".pdf")
    canvas.Clear()

    # Reset legend
    leg = ROOT.TLegend(0.2, 0.5, 0.3, 0.65)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.03)
    leg.SetEntrySeparation(0.001)
    for i, key in enumerate(delta_phi_ll_histograms):
      hist = delta_phi_ll_histograms[key]
      leg.AddEntry(hist, key, "l")

    stacked_hist.Draw("hist")
    leg.Draw('SAME')
    stacked_hist.GetXaxis().SetTitle(delta_phi_ll_histograms["llll"].GetXaxis().GetTitle())
    stacked_hist.GetYaxis().SetTitle(delta_phi_ll_histograms["llll"].GetYaxis().GetTitle())
    canvas.SaveAs("signedDeltaPhill/stack_" + cut + ".pdf")
    canvas.Clear()
    ### END OF PLOTTING ###

    ### SIGNIFICANCE PLOTTING ###
    sig_1 = delta_phi_ll_histograms["signal"].Clone("SBsignal1" + cut)
    total_background = delta_phi_ll_histograms["llll"].Clone("SBbackground" + cut)
    total_background.Add(delta_phi_ll_histograms["other di-boson"])
    total_background.Add(delta_phi_ll_histograms["jets"])

    for i in range(1, sig_1.GetNbinsX() + 1):
      sig_1.SetBinContent(i, significance_calc(i, delta_phi_ll_histograms["signal"], total_background))

    sig_1.SetMaximum(sig_1.GetBinContent(sig_1.GetMaximumBin())*1.1)
    sig_1.SetLineWidth(3)
    sig_1.SetMarkerColor(ROOT.kRed)
    sig_1.SetLineColor(ROOT.kRed)
    sig_1.Draw('hist')
    sig_1.GetYaxis().SetTitle("S/#sqrt{S+B}")

    canvas.SaveAs("signedDeltaPhill/SoverSqrtSB" + cut + ".pdf")
    canvas.Clear()
    ### END OF SB RATIO PLOTTING ###

if __name__ == "__main__":
  main()
