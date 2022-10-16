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
  pTt0 = ROOT.TH1D("tau0_pt","p_{T}^{#tau_0}" ,150,0 ,300)
  pTt0.Sumw2()
  pTt1 = pTt0.Clone("tau1_pt")
  pTt1.SetTitle("p_{T}^{#tau_1}")

  for i in range(0,tree.GetEntries()):
    tree.GetEntry(i)
    #vector of TLorentzVectors of the taus
    taus_p4 = getattr(tree, "taus_p4")
    # we need to have at least 2 taus
    if len(taus_p4) > 1:
      pt = taus_p4[0].Pt()
      pTt0.Fill(pt)
      pt = taus_p4[1].Pt()
      pTt1.Fill(pt)
      #print(pt)

  if (args.outputfile[-5:] != ".root"):
    args.outputfile += ".root"
  outHistFile = ROOT.TFile.Open(args.outputfile, "RECREATE")
  outHistFile.cd()
  pTt0.Write()
  pTt1.Write()
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
