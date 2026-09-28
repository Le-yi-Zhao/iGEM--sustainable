import java.nio.file.*;
import java.io.*;
import java.util.*;
import insilico.models.dispatcher.ModelDispatcher;
import insilico.core.model.runner.*;
import insilico.core.model.report.txt.ReportTXTSingle;
import insilico.core.molecule.InsilicoMolecule;
import insilico.core.molecule.conversion.SmilesMolecule;

/** Headless execution of the official VEGA 1.2.6 bundle; no model reimplementation. */
public class GalateaVega {
  public static void main(String[] args) throws Exception {
    var dataset = new ArrayList<InsilicoMolecule>();
    for (String line : Files.readAllLines(Path.of(args[0]))) {
      String[] fields = line.split("\t", -1);
      InsilicoMolecule molecule = SmilesMolecule.Convert(fields[1]);
      molecule.SetId(fields[0]);
      if (!molecule.IsValid()) throw new IllegalArgumentException("Invalid compound " + fields[0]);
      dataset.add(molecule);
    }
    Files.createDirectories(Path.of(args[1]));
    String[] fields = {"MUTA_CAESAR", "SKIN_CAESAR", "BCF_CAESAR", "BCF_MEYLAN", "BCF_ARNOTGOBAS", "READYBIO_IRFMN", "LOGP_MEYLAN", "FISH_LC50", "DAPHNIA_EC50", "ALGAE_EC50"};
    int failures = 0;
    for (String field : fields) {
      System.out.println("START " + field);
      try {
        String tag = (String) ModelDispatcher.class.getField(field).get(null);
        var model = ModelDispatcher.GetModelFromTag(tag);
        var runner = new InsilicoModelRunnerByMolecule();
        runner.setMessenger(new iInsilicoModelRunnerMessenger() {
          public void SendMessage(String text) { System.out.println(text); }
          public void UpdateProgress() {}
        });
        runner.AddModel(model);
        runner.Run(dataset);
        try (var writer = new PrintWriter(Files.newBufferedWriter(Path.of(args[1], field + ".txt")))) {
          ReportTXTSingle.PrintReport(dataset, runner.GetModelWrappers().get(0), writer);
        }
        System.out.println("COMPLETE " + field);
      } catch (Exception ex) {
        failures++;
        ex.printStackTrace();
        System.out.println("FAILED " + field);
      }
    }
    if (failures > 0) throw new RuntimeException(failures + " selected VEGA models failed");
  }
}
