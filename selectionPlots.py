import ROOT
import copy, os, re, sys
import argparse
import math

Zmass = 91.1876

## Method to resolve regular expressions in file names.
#  TChain::Add only supports wildcards in the last items, i.e. on file level.
#  This method can resolve all wildcards at any directory level,
#  e.g. /my/directory/a*test*/pattern/*.root
#  @param pattern    the file name pattern using python regular expressions
#  @return list of all files matching the pattern
def findAllFilesInPath( pattern ,path ):
  files = []
  items = pattern.split( '/' )

  def checkPath( path, items ):
    # nested method to deal with the recursion
    import ROOT
    if not items:
      return
    myItems = copy.copy( items )
    item = myItems.pop(0)
    if '*' in item:
      directory = ROOT.gSystem.OpenDirectory( path )
      # beg and end of line control so that *truc does not match bla_truc_xyz
      item = "^"+item.replace( '*', '.*' )+"$"
      p = re.compile( item )
      entry = True
      while entry:
        entry = ROOT.gSystem.GetDirEntry( directory )
        if p.match( entry ):
          if not myItems:
            files.append( path + entry )
          else:
            checkPath( path + entry + '/', myItems)
      ROOT.gSystem.FreeDirectory( directory )
    elif item and not myItems:
      files.append( path + item )
    else:
      checkPath( path + item + '/', myItems )
  checkPath( path, items )
  return files

def fillHistograms(tau1, tauOrLep, Zlep1, Zlep2, met_p4, nJets, totalWeight, cut):
  pt = tau1.Pt() + tauOrLep.Pt()
  leptonMass = (Zlep1 + Zlep2).M()
  dRZ = Zlep1.DeltaR(Zlep2)
  dRH = tau1.DeltaR(tauOrLep)
  dEtaZ = math.fabs(Zlep1.Eta() - Zlep2.Eta())
  dEtaH = math.fabs(tau1.Eta() - tauOrLep.Eta())
  dRtauL = (tau1 + tauOrLep).DeltaR(Zlep1 + Zlep2)

  if cut == "di":
    diLepPTtsum.Fill(pt, totalWeight)
    diLepDiLeptonMass.Fill(leptonMass, totalWeight)
    diLepMetpT.Fill(met_p4, totalWeight)
    diLepDeltaRZ.Fill(dRZ, totalWeight)
    diLepDeltaRH.Fill(dRH, totalWeight)
    diLepDeltaEtaZ.Fill(dEtaZ, totalWeight)
    diLepDeltaEtaH.Fill(dEtaH, totalWeight)
    diLepDeltaRtauL.Fill(dRtauL, totalWeight)
    diLepNJets.Fill(nJets, totalWeight)
    diLepDeltaPhiZ.Fill(, totalWeight)
    diLepDeltaPhiH.Fill(, totalWeight)
  elif cut == "tri":
    triLepPTtsum.Fill(pt, totalWeight)
    triLepDiLeptonMass.Fill(leptonMass, totalWeight)
    triLepMetpT.Fill(met_p4, totalWeight)
    triLepDeltaRZ.Fill(dRZ, totalWeight)
    triLepDeltaRH.Fill(dRH, totalWeight)
    triLepDeltaEtaZ.Fill(dEtaZ, totalWeight)
    triLepDeltaEtaH.Fill(dEtaH, totalWeight)
    triLepDeltaRtauL.Fill(dRtauL, totalWeight)
    triLepNJets.Fill(nJets, totalWeight)
    triLepDeltaPhiZ.Fill(, totalWeight)
    triLepDeltaPhiH.Fill(, totalWeight)

def main(args):
  if (args.inputsample[-1] != "/"): #adds / to end of file path if not present
    args.inputsample += "/"
  directory = "Ztt/"+args.inputsample
  pattern = "*.root"

  tree = ROOT.TChain("NOMINAL")
  nFiles = 0
  luminosity = 140000
  sumAllMC = 0
  for fileName in findAllFilesInPath(pattern, directory):
    nFiles += tree.Add(fileName)
    file = ROOT.TFile.Open(fileName)
    h = file.Get("h_metadata")
    sumAllMC += h.GetBinContent(8)
    file.Close()
  print(nFiles, "files")

  # define histograms
  global diLepPTtsum, diLepDiLeptonMass, diLepMetpT, diLepDeltaRZ, diLepDeltaRH, diLepDeltaEtaZ, diLepDeltaEtaH,
  diLepDeltaRtauL, diLepNJets, diLepDeltaPhiZ, diLepDeltaPhiH

  diLepPTtsum = ROOT.TH1D("2_lep_tau_pt_sum", "p_{T}^{#tau_sum};pT(GeV);Counts", 200, 0, 500)
  diLepDiLeptonMass = ROOT.TH1D("2_lep_lepton_mass_sum", "M(ll);Mass(GeV);Counts", 150, 0, 200)
  diLepMetpT = ROOT.TH1D("2_lep_met_pt", "met.Pt();pT(GeV);Counts", 150, 0, 500)
  diLepDeltaRZ = ROOT.TH1D("2_lep_delta_R_Z", "delta_R_Z;Delta R;Counts", 150, 0, 5)
  diLepDeltaRH = ROOT.TH1D("2_lep_delta_R_H", "delta_R_H;Delta R;Counts", 150, 0, 5)
  diLepDeltaEtaZ = ROOT.TH1D("2_lep_delta_Eta_Z", "delta_Eta_Z;Delta Eta;Counts", 150, 0, 5)
  diLepDeltaEtaH = ROOT.TH1D("2_lep_delta_Eta_H", "delta_Eta_H;Delta Eta;Counts", 150, 0, 5)
  diLepDeltaRtauL = ROOT.TH1D("2_lep_delta_R_tau_l", "delta_R_tl;Delta R;Counts", 150, 0, 5)
  diLepNJets = ROOT.TH1D("2_lep_n_jets", "n_jets;n_jets;Counts", 10, 0, 10)
  diLepDeltaPhiZ = ROOT.TH1D("2_lep_delta_phi_Z", "delta_phi_Z;Delta Phi; Counts", 150, -4, 4)
  diLepDeltaPhiH = ROOT.TH1D("2_lep_delta_phi_H", "delta_phi_H;Delta Phi; Counts", 150, -4, 4)
  # diLepPTtsum.Sumw2()
  # diLepDiLeptonMass.Sumw2()
  # diLepMetpT.Sumw2()
  # diLepDeltaRZ.Sumw2()
  # diLepDeltaRH.Sumw2()
  # diLepDeltaEtaZ.Sumw2()
  # diLepDeltaEtaH.Sumw2()
  # diLepDeltaRtauL.Sumw2()
  global triLepPTtsum, triLepDiLeptonMass, triLepMetpT, triLepDeltaRZ, triLepDeltaRH, triLepDeltaEtaZ, triLepDeltaEtaH,
  triLepDeltaRtauL, triLepNJets, triLepDeltaPhiZ, triLepDeltaPhiH

  triLepPTtsum = diLepPTtsum.Clone("3_lep_tau_pt_sum")
  triLepDiLeptonMass = diLepDiLeptonMass.Clone("3_lep_Z_lepton_mass_sum")
  triLepMetpT = diLepMetpT.Clone("3_lep_met_pt")
  triLepDeltaRZ = diLepDeltaRZ.Clone("3_lep_delta_R_Z")
  triLepDeltaRH = diLepDeltaRH.Clone("3_lep_delta_R_H")
  triLepDeltaEtaZ = diLepDeltaEtaZ.Clone("3_lep_delta_Eta_Z")
  triLepDeltaEtaH = diLepDeltaEtaH.Clone("3_lep_delta_Eta_H")
  triLepDeltaRtauL = diLepDeltaRtauL.Clone("3_lep_delta_R_tau_l")
  triLepNJets = diLepNJets.Clone("3_lep_n_jets")
  triLepDeltaPhiZ = diLepDeltaPhiZ.Clone("3_lep_delta_phi_Z")
  triLepDeltaPhiH = diLepDeltaPhiH.Clone("3_lep_delta_phi_H")

  #FILL HISTOGRAMS LOOP
  for i in range(0, tree.GetEntries()):
    tree.GetEntry(i)
    # vector of TLorentzVectors of the taus
    taus_p4 = getattr(tree, "taus_p4")
    leptons_p4 = getattr(tree, "leptons_p4")
    met_p4 = getattr(tree, "met_p4")
    nJets30 = getattr(tree, "n_jets_30")
    lFlavour = getattr(tree, "leptons")
    lCharge = getattr(tree, "leptons_q")
    crossSection = getattr(tree, "cross_section")
    weight = getattr(tree, "pu_NOMINAL_pileup_combined_weight") * getattr(tree, "weight_mc")

    # we need to have at least 2 taus
    if len(taus_p4) > 1:
      # selection cut for 2 lepton final state
      if (len(leptons_p4) == 2) and (lFlavour[0] == lFlavour[1]) and (lCharge[0] == -lCharge[1]):
        wTotal = (weight/sumAllMC) * crossSection * luminosity
        fillHistograms(taus_p4[0], taus_p4[1], leptons_p4[0], leptons_p4[1], diLepPTtsum, diLepDiLeptonMass,
         diLepDeltaRZ, diLepDeltaRH, diLepDeltaEtaZ, diLepDeltaEtaH, diLepMetpT, diLepDeltaRtauL, diLepNJets,
          met_p4.Pt(), nJets30, wTotal)

      # selection cut for 3 lepton final state
      elif (len(leptons_p4) == 3):
        flavList = [lFlavour[0], lFlavour[1], lFlavour[2]]
        chargeList = [lCharge[0], lCharge[1], lCharge[2]]

        if (flavList.count(1) == 1) and (flavList.count(2) == 2): # One muon, two electrons. Could do sum(flavList) == 5
          index = flavList.index(1)

        elif (flavList.count(2) == 1) and (flavList.count(1) == 2): # Two muons, one electron. Could do sum(flavList) == 4
          index = flavList.index(2)

        elif (chargeList.count(+1) == 1) and (chargeList.count(-1) == 2): # One positive charge, two negatives
          posIndex = chargeList.index(+1)
          if math.fabs((leptons_p4[posIndex] + leptons_p4[(posIndex + 1)%3]).M() - Zmass) < math.fabs((leptons_p4[posIndex]
           + leptons_p4[(posIndex - 1)%3]).M() - Zmass):
            wTotal = (weight/sumAllMC) * crossSection * luminosity
            fillHistograms(taus_p4[0], leptons_p4[(posIndex - 1)%3], leptons_p4[posIndex],
             leptons_p4[(posIndex + 1)%3], triLepPTtsum, triLepDiLeptonMass, triLepDeltaRZ, triLepDeltaRH, triLepDeltaEtaZ,
              triLepDeltaEtaH, triLepMetpT, triLepDeltaRtauL, triLepNJets, met_p4.Pt(), nJets30, wTotal)
            continue

          else:
            wTotal = (weight/sumAllMC) * crossSection * luminosity
            fillHistograms(taus_p4[0], leptons_p4[(posIndex + 1)%3], leptons_p4[posIndex],
             leptons_p4[(posIndex - 1)%3], triLepPTtsum, triLepDiLeptonMass, triLepDeltaRZ, triLepDeltaRH, triLepDeltaEtaZ,
              triLepDeltaEtaH, triLepMetpT, triLepDeltaRtauL, triLepNJets, met_p4.Pt(), nJets30, wTotal)
            continue

        elif (chargeList.count(-1) == 1) and (chargeList.count(+1) == 2): # Two positive charges, one negative
          negIndex = chargeList.index(-1)
          if math.fabs((leptons_p4[negIndex] + leptons_p4[(negIndex + 1)%3]).M() - Zmass) < math.fabs((leptons_p4[negIndex]
           + leptons_p4[(negIndex - 1)%3]).M() - Zmass):
            wTotal = (weight/sumAllMC) * crossSection * luminosity
            fillHistograms(taus_p4[0], leptons_p4[(negIndex - 1)%3], leptons_p4[negIndex],
             leptons_p4[(negIndex + 1)%3], triLepPTtsum, triLepDiLeptonMass, triLepDeltaRZ, triLepDeltaRH, triLepDeltaEtaZ,
              triLepDeltaEtaH, triLepMetpT, triLepDeltaRtauL, triLepNJets, met_p4.Pt(), nJets30, wTotal)
            continue

          else:
            wTotal = (weight/sumAllMC) * crossSection * luminosity
            fillHistograms(taus_p4[0], leptons_p4[(negIndex + 1)%3], leptons_p4[negIndex],
             leptons_p4[(negIndex - 1)%3], triLepPTtsum, triLepDiLeptonMass, triLepDeltaRZ, triLepDeltaRH, triLepDeltaEtaZ,
              triLepDeltaEtaH, triLepMetpT, triLepDeltaRtauL, triLepNJets, met_p4.Pt(), nJets30, wTotal)
            continue

        wTotal = (weight/sumAllMC) * crossSection * luminosity
        fillHistograms(taus_p4[0], leptons_p4[index], leptons_p4[(index + 1)%3], leptons_p4[(index - 1)%3],
         triLepPTtsum, triLepDiLeptonMass, triLepDeltaRZ, triLepDeltaRH, triLepDeltaEtaZ, triLepDeltaEtaH, triLepMetpT,
          triLepDeltaRtauL, triLepNJets, met_p4.Pt(), nJets30, wTotal)



  if (args.outputfile[-5:] != ".root"): #adds .root to end of output file if not present
    args.outputfile += ".root"
  outHistFile = ROOT.TFile.Open(args.outputfile, "RECREATE")
  outHistFile.cd()

  diLepPTtsum.Write()
  diLepDiLeptonMass.Write()
  diLepMetpT.Write()
  diLepDeltaRZ.Write()
  diLepDeltaRH.Write()
  diLepDeltaEtaZ.Write()
  diLepDeltaEtaH.Write()
  diLepDeltaRtauL.Write()
  diLepNJets.Write()

  triLepPTtsum.Write()
  triLepDiLeptonMass.Write()
  triLepMetpT.Write()
  triLepDeltaRZ.Write()
  triLepDeltaRH.Write()
  triLepDeltaEtaZ.Write()
  triLepDeltaEtaH.Write()
  triLepDeltaRtauL.Write()
  triLepNJets.Write()

  outHistFile.Close()

  del tree

if __name__ == "__main__":
  # parse the CLI arguments
  parser = argparse.ArgumentParser(description='script to run over ntuple dataset')
  parser.add_argument('--inputsample', '-i', metavar='INPUT', type=str, dest="inputsample", default="ZHlltt/", help='directory for input root files')
  parser.add_argument('--outputfile', '-o', metavar='OUTPUT', type=str, dest="outputfile", default="lltautauhistograms.root", help='outputfile for process')
  args = parser.parse_args()

  # call the main function
  main(args)
