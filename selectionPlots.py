import ROOT
import copy, os, re, sys
import argparse


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


def main(args):
  if (args.inputsample[-1] != "/"): #adds / to end of file path if not present
    args.inputsample += "/"
  directory = "Ztt/"+args.inputsample
  pattern = "*.root"

  tree = ROOT.TChain( "NOMINAL" )
  nFiles = 0
  for fileName in findAllFilesInPath( pattern, directory ):
    nFiles += tree.Add( fileName )
  print(nFiles, "files")

  # define histograms
  pTtsum = ROOT.TH1D("tau_pt_sum", "p_{T}^{#tau_sum}", 200, 0, 500)
  diLeptonMass = ROOT.TH1D("lepton_mass_sum", "M(ll)", 150, 0, 200)
  metpTsum = ROOT.TH1D("met_pt_sum", "met.Pt()_sum", 150, 0, 500)
  deltaRZ = ROOT.TH1D("delta_R_Z", "delta_R_Z", 150, 0, 5)
  deltaRH = ROOT.TH1D("delta_R_H", "delta_R_H", 150, 0, 5)
  deltaEtaZ = ROOT.TH1D("delta_Eta_Z", "delta_Eta_Z", 150, 0, 5)
  deltaEtaH = ROOT.TH1D("delta_Eta_H", "delta_Eta_H", 150, 0, 5)
  pTtsum.Sumw2()
  diLeptonMass.Sumw2()
  metpTsum.Sumw2()
  deltaRZ.Sumw2()
  deltaRH.Sumw2()
  deltaEtaZ.Sumw2()
  deltaEtaH.Sumw2()

  #FILL HISTOGRAMS LOOP
  for i in range(0, tree.GetEntries()):
    tree.GetEntry(i)
    # vector of TLorentzVectors of the taus
    taus_p4 = getattr(tree, "taus_p4")
    leptons_p4 = getattr(tree, "leptons_p4")
    met_p4 = getattr(tree, "met_p4")
    lFlavour = getattr(tree, "leptons")
    lCharge = getattr(tree, "leptons_q")

    # we need to have at least 2 taus
    if len(taus_p4) > 1:
      # selection cut for 2 leptons in final state
      if (len(leptons_p4) == 2) and (lFlavour[0] == lFlavour[1]) and (lCharge[0] == -lCharge[1]):
        pt = taus_p4[0].Pt() + taus_p4[1].Pt()
        leptonMass = (leptons_p4[0] + leptons_p4[1]).M() # maybe faster to do (leptons_p4[0].M() + leptons_p4[1].M())?
        dRZ = leptons_p4[0].DeltaR(leptons_p4[1])
        dRH = taus_p4[0].DeltaR(taus_p4[1])
        dEtaZ = leptons_p4[0].DeltaR(leptons_p4[1])
        dEtaH = taus_p4[0].DeltaR(taus_p4[1])

        pTtsum.Fill(pt)
        diLeptonMass.Fill(leptonMass)
        metpTsum.Fill(met_p4.Pt())
        deltaRZ.Fill(dRZ)
        deltaRH.Fill(dRH)
        deltaEtaZ.Fill(dEtaZ)
        deltaEtaH.Fill(dEtaH)

      # selection cut for 3 leptons in final state
      #elif (len(leptons_p4) == 3) and (lFlavour[0] )

  #OUTPUT LOOP
  if (args.outputfile[-5:] != ".root"): #adds .root to end of output file if not present
    args.outputfile += ".root"
  outHistFile = ROOT.TFile.Open(args.outputfile, "RECREATE")
  outHistFile.cd()

  pTtsum.Write()
  diLeptonMass.Write()
  metpTsum.Write()
  deltaRZ.Write()
  deltaRH.Write()
  deltaEtaZ.Write()
  deltaEtaH.Write()

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
