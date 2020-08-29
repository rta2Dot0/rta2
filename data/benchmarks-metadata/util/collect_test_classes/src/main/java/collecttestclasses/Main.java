package collecttestclasses;

import java.io.File;
import java.io.FileInputStream;
import java.io.PrintWriter;
import java.lang.reflect.Modifier;
import java.util.LinkedHashSet;
import java.util.Set;
import org.apache.commons.io.FileUtils;
import javassist.ClassPool;
import javassist.CtBehavior;
import javassist.CtClass;
import javassist.NotFoundException;

public class Main {

  private static final ClassPool classPool = ClassPool.getDefault();

  public static void main(String[] args) throws Exception {

    /**
     * Args
     */
    if (args.length != 2) {
      throw new RuntimeException(
          "Usage: " + Main.class.getCanonicalName() + " <tests dir path> <output file path>!");
    }

    final File path = new File(args[0]);
    if (!path.exists()) {
      throw new RuntimeException("File/Directory '" + path.getAbsolutePath() + "' does not exist!");
    }
    if (!path.canRead()) {
      throw new RuntimeException(
          "No permission to read file/directory '" + path.getAbsolutePath() + "'!");
    }

    final File outputFile = new File(args[1]);
    if (!outputFile.exists()) {
      outputFile.delete();
    }

    /**
     * Find test classes
     */

    Set<String> testClasses = new LinkedHashSet<String>();

    for (File class_file : FileUtils.listFiles(path, new String[] {"class"}, true)) {
      FileInputStream fin = new FileInputStream(class_file);
      CtClass ctClass = classPool.makeClassIfNew(fin);

      // Is it an anonymous or inner class?
      if (ctClass.getName().contains("$")) {
        continue;
      }

      // Is it an abstract class?
      if ((ctClass.getModifiers() & Modifier.ABSTRACT) != 0) {
        continue;
      }

      // Is it an interface?
      if ((ctClass.getModifiers() & Modifier.INTERFACE) != 0) {
        continue;
      }

      // Is it public or default?
      if (((ctClass.getModifiers() & Modifier.PUBLIC) != 0) || (ctClass.getModifiers() == 0)) {

        if (superClassMatcher(ctClass)) {
          // JUnit 3 test classes
          testClasses.add(ctClass.getName());
        } else {
          // JUnit >3 test classes or TestNG test classes
          for (CtBehavior ctBehavior : ctClass.getMethods()) {
            if (ctBehavior.hasAnnotation("org.junit.Test")
                || ctBehavior.hasAnnotation("org.junit.experimental.theories.Theory")
                || ctBehavior.hasAnnotation("org.junit.jupiter.api.Test")
                || ctBehavior.hasAnnotation("org.testng.annotations.Test")) {
              testClasses.add(ctClass.getName());
            }
          }
        }

      }

      ctClass.detach();
      fin.close();
    }

    /**
     * Print out test classes
     */

    PrintWriter testsWriter = new PrintWriter(outputFile, "UTF-8");
    for (String testClass : testClasses) {
      testsWriter.println(testClass);
    }
    testsWriter.close();

    System.exit(0);
  }

  public static boolean superClassMatcher(final CtClass ctClass) throws NotFoundException {
    CtClass superCtClass = ctClass.getSuperclass();
    while (superCtClass != null) {
      if (superCtClass.getName().equals("junit.framework.TestCase")) {
        return true;
      }
      superCtClass = superCtClass.getSuperclass();
    }
    return false;
  }

}
