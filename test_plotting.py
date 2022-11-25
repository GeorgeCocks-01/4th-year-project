from ROOT import *
import copy, os, re, sys
import argparse

gROOT.LoadMacro('../atlasrootstyle/AtlasStyle.C')
gROOT.LoadMacro('../atlasrootstyle/AtlasUtils.C')
gROOT.SetBatch(kTRUE)
SetAtlasStyle()

canv = TCanvas('c','c',600,600)
canv.cd()
colorList = [kBlack,kRed,kBlue,kGreen,kViolet,kMagenta,kAzure,kOrange,kYellow,kMagenta+3,kCyan,kYellow+2]

samples = [('ZH','outputRoot/ZH-weighted.root', kRed),
       ('ZqqZll', 'outputRoot/ZqqZll-weighted.root', kBlue),
       ('ggZH', 'outputRoot/ggZH-weighted.root', kGreen),
       ('llll', 'outputRoot/llll-weighted.root', kMagenta),
       ('lllv', 'outputRoot/lllv-weighted.root', kAzure),
       ('llvv', 'outputRoot/llvv-weighted.root', kOrange),
       ('ttH', 'outputRoot/ttH-weighted.root', kYellow),
       ('WqqZll', 'outputRoot/WqqZll-weighted.root', kBlack)]

varList = ["tau_pt_sum", "Z_lepton_mass_sum", "met_pt", "delta_R_ll", "delta_R_tt",
"delta_Eta_ll", "delta_Eta_tt", "delta_R_tt_ll", "n_jets", "delta_phi_ll",
"delta_phi_tt", "delta_phi_ll_tt", "mmc_mass"]

for i in range(2,4):
  cut = str(i) + "_lep_"
  for var in varList:
    var = cut + var
    leg = TLegend(0.7,0.6,0.8,0.85)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.03)
    leg.SetEntrySeparation(0.001)

    counter = 0
    histos=[]
    legnames=[]
    maximum = -999.
    stackedHisto = THStack()
    for sample in samples:
      infile = TFile.Open(sample[1],"READ")
      histo = infile.Get(var)
      histo.SetDirectory(0)
      infile.Close()
      legName = sample[0]

      stackedHisto.Add(histo)
      histo.Scale(1/histo.Integral())

      if histo.GetMaximum() > maximum:
        maximum = histo.GetMaximum()

      histo.SetLineWidth(3)
      histo.SetMarkerColor(sample[2])
      histo.SetLineColor(sample[2])
      histos.append(histo)

      legnames.append(legName)

    for i in range(0, len(histos)):
      if i == 0:
        histos[i].SetMaximum(maximum * 1.3)
        histos[i].Draw('hist')
      else:
        histos[i].Draw('histSAME')

      leg.AddEntry(histos[i],legnames[i], 'l')


    leg.Draw('SAME')

    #myText(0.19,0.76,kBlack,'#sqrt{s} = 13 TeV, 140 fb^{-1}')

    canv.SaveAs('plots/' + var + '.pdf')
    canv.Clear()
    # stackedHisto.SetLineWidth(3)
    # stackedHisto.SetMarkerColor(sample[2])
    # stackedHisto.SetLineColor(sample[2])

    # stackedHisto.SetMaximum(maximum * 1.3)
    stackedHisto.Draw('hist')
    leg.Draw('SAME')
    canv.SaveAs('stackPlots/stack_' + var + '.pdf')
