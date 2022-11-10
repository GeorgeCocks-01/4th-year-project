from ROOT import *
import copy, os, re, sys
import argparse

gROOT.LoadMacro('../atlasrootstyle/AtlasStyle.C')
gROOT.LoadMacro('../atlasrootstyle/AtlasUtils.C')
gROOT.SetBatch(kTRUE)
SetAtlasStyle()

canv = TCanvas('c','c',600,600)
canv.cd()
colorList = [kBlack,kRed,kBlue,kGreen,kViolet,kMagenta,kAzure,kViolet,kOrange,kYellow,kMagenta+3,kCyan,kYellow+2]

samples = [('ZH','Ztt/ZH-weighted.root', kRed),
       ('ZZ', 'Ztt/ZZ-weighted.root', kBlue)]

varList = ["2_lep_tau_pt_sum", "2_lep_lepton_mass_sum", "2_lep_met_pt", "2_lep_delta_R_Z", "2_lep_delta_R_H",
"2_lep_delta_Eta_Z", "2_lep_delta_Eta_H", "2_lep_delta_R_tau_l", "2_lep_n_jets", "2_lep_delta_phi_Z",
"2_lep_delta_phi_H", "2_lep_delta_phi_tau_l", "3_lep_tau_pt_sum", "3_lep_Z_lepton_mass_sum", "3_lep_met_pt",
"3_lep_delta_R_Z", "3_lep_delta_R_H", "3_lep_delta_Eta_Z", "3_lep_delta_Eta_H",  "3_lep_delta_R_tau_l", "3_lep_n_jets",
"3_lep_delta_phi_Z", "3_lep_delta_phi_H", "3_lep_delta_phi_tau_l"]

for var in varList:
  leg = TLegend(0.7,0.7,0.8,0.85)
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

    histo.Scale(1/histo.Integral())

    if histo.GetMaximum() > maximum:
      maximum = histo.GetMaximum()

    histo.SetLineWidth(3)
    histo.SetMarkerColor(sample[2])
    histo.SetLineColor(sample[2])
    histos.append(histo)
    stackedHisto.Add(histo)
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
