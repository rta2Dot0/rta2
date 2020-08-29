/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.commons.math3.random;

import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

import org.apache.commons.math3.Retry;
import org.apache.commons.math3.RetryRunner;
import org.apache.commons.math3.TestUtils;
import org.apache.commons.math3.distribution.BetaDistribution;
import org.apache.commons.math3.distribution.BinomialDistribution;
import org.apache.commons.math3.distribution.BinomialDistributionTest;
import org.apache.commons.math3.distribution.CauchyDistribution;
import org.apache.commons.math3.distribution.ChiSquaredDistribution;
import org.apache.commons.math3.distribution.ExponentialDistribution;
import org.apache.commons.math3.distribution.FDistribution;
import org.apache.commons.math3.distribution.GammaDistribution;
import org.apache.commons.math3.distribution.HypergeometricDistribution;
import org.apache.commons.math3.distribution.HypergeometricDistributionTest;
import org.apache.commons.math3.distribution.NormalDistribution;
import org.apache.commons.math3.distribution.PascalDistribution;
import org.apache.commons.math3.distribution.PascalDistributionTest;
import org.apache.commons.math3.distribution.PoissonDistribution;
import org.apache.commons.math3.distribution.TDistribution;
import org.apache.commons.math3.distribution.WeibullDistribution;
import org.apache.commons.math3.distribution.ZipfDistribution;
import org.apache.commons.math3.distribution.ZipfDistributionTest;
import org.apache.commons.math3.stat.Frequency;
import org.apache.commons.math3.stat.descriptive.SummaryStatistics;
import org.apache.commons.math3.stat.inference.ChiSquareTest;
import org.apache.commons.math3.util.FastMath;
import org.apache.commons.math3.exception.MathIllegalArgumentException;
import org.junit.Assert;
import org.junit.Test;
import org.junit.runner.RunWith;

/**
 * Test cases for the RandomDataGenerator class.
 *
 * @version $Id$
 */
@RunWith(RetryRunner.class)
public class RandomDataGeneratorTest {

    public RandomDataGeneratorTest() {
        randomData = new RandomDataGenerator();
        randomData.reSeed(1000);
    }

    protected final long smallSampleSize = 1000;
    protected final double[] expected = { 250, 250, 250, 250 };
    protected final int largeSampleSize = 10000;
    private final String[] hex = { "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "a", "b", "c", "d", "e", "f" };
    protected RandomDataGenerator randomData = null;
    protected final ChiSquareTest testStatistic = new ChiSquareTest();

    @Test
    public void testNextIntExtremeValues() {
    }

    @Test
    public void testNextLongExtremeValues() {
    }
    
    @Test
    public void testNextUniformExtremeValues() {
    }
    
    @Test
    public void testNextIntIAE() {
    }
    
    @Test
    public void testNextIntNegativeToPositiveRange() {
    }

    @Test 
    public void testNextIntNegativeRange() {
    }

    @Test 
    public void testNextIntPositiveRange() {
    }

    private void checkNextIntUniform(int min, int max) {
        final Frequency freq = new Frequency();
        for (int i = 0; i < smallSampleSize; i++) {
            final int value = randomData.nextInt(min, max);
            Assert.assertTrue("nextInt range", (value >= min) && (value <= max));
            freq.addValue(value);
        }
        final int len = max - min + 1;
        final long[] observed = new long[len];
        for (int i = 0; i < len; i++) {
            observed[i] = freq.getCount(min + i);
        }
        final double[] expected = new double[len];
        for (int i = 0; i < len; i++) {
            expected[i] = 1d / len;
        }
        
        TestUtils.assertChiSquareAccept(expected, observed, 0.001);
    }

    @Test
    public void testNextIntWideRange() {
    }
    
    @Test
    public void testNextLongIAE() {
    }

    @Test
    public void testNextLongNegativeToPositiveRange() {
    }

    @Test 
    public void testNextLongNegativeRange() {
    }

    @Test 
    public void testNextLongPositiveRange() {
    }

    private void checkNextLongUniform(long min, long max) {
        final Frequency freq = new Frequency();
        for (int i = 0; i < smallSampleSize; i++) {
            final long value = randomData.nextLong(min, max);
            Assert.assertTrue("nextLong range: " + value + " " + min + " " + max,
                              (value >= min) && (value <= max));
            freq.addValue(value);
        }
        final int len = ((int) (max - min)) + 1;
        final long[] observed = new long[len];
        for (int i = 0; i < len; i++) {
            observed[i] = freq.getCount(min + i);
        }
        final double[] expected = new double[len];
        for (int i = 0; i < len; i++) {
            expected[i] = 1d / len;
        }
        
        TestUtils.assertChiSquareAccept(expected, observed, 0.01);
    }

    @Test
    public void testNextLongWideRange() {
    }
    
    @Test
    public void testNextSecureLongIAE() {
    }
    
    @Test
    @Retry(3)
    public void testNextSecureLongNegativeToPositiveRange() {
    }
    
    @Test
    @Retry(3)
    public void testNextSecureLongNegativeRange() {
    }
    
    @Test
    @Retry(3)
    public void testNextSecureLongPositiveRange() {
    }
    
    private void checkNextSecureLongUniform(int min, int max) {
        final Frequency freq = new Frequency();
        for (int i = 0; i < smallSampleSize; i++) {
            final long value = randomData.nextSecureLong(min, max);
            Assert.assertTrue("nextLong range", (value >= min) && (value <= max));
            freq.addValue(value);
        }
        final int len = max - min + 1;
        final long[] observed = new long[len];
        for (int i = 0; i < len; i++) {
            observed[i] = freq.getCount(min + i);
        }
        final double[] expected = new double[len];
        for (int i = 0; i < len; i++) {
            expected[i] = 1d / len;
        }
        
        TestUtils.assertChiSquareAccept(expected, observed, 0.0001);
    }

    @Test
    public void testNextSecureIntIAE() {
    }
    
    @Test
    @Retry(3)
    public void testNextSecureIntNegativeToPositiveRange() {
    }
    
    @Test
    @Retry(3)
    public void testNextSecureIntNegativeRange() {
    }
    
    @Test 
    @Retry(3)
    public void testNextSecureIntPositiveRange() {
    }
     
    private void checkNextSecureIntUniform(int min, int max) {
        final Frequency freq = new Frequency();
        for (int i = 0; i < smallSampleSize; i++) {
            final int value = randomData.nextSecureInt(min, max);
            Assert.assertTrue("nextInt range", (value >= min) && (value <= max));
            freq.addValue(value);
        }
        final int len = max - min + 1;
        final long[] observed = new long[len];
        for (int i = 0; i < len; i++) {
            observed[i] = freq.getCount(min + i);
        }
        final double[] expected = new double[len];
        for (int i = 0; i < len; i++) {
            expected[i] = 1d / len;
        }
        
        TestUtils.assertChiSquareAccept(expected, observed, 0.0001);
    }
    
    

    /**
     * Make sure that empirical distribution of random Poisson(4)'s has P(X <=
     * 5) close to actual cumulative Poisson probability and that nextPoisson
     * fails when mean is non-positive.
     */
    @Test
    public void testNextPoisson() {
    }

    @Test
    public void testNextPoissonConsistency() {
    }

    /**
     * Verifies that nextPoisson(mean) generates an empirical distribution of values
     * consistent with PoissonDistributionImpl by generating 1000 values, computing a
     * grouped frequency distribution of the observed values and comparing this distribution
     * to the corresponding expected distribution computed using PoissonDistributionImpl.
     * Uses ChiSquare test of goodness of fit to evaluate the null hypothesis that the
     * distributions are the same. If the null hypothesis can be rejected with confidence
     * 1 - alpha, the check fails.
     */
    public void checkNextPoissonConsistency(double mean) {
        // Generate sample values
        final int sampleSize = 1000;        // Number of deviates to generate
        final int minExpectedCount = 7;     // Minimum size of expected bin count
        long maxObservedValue = 0;
        final double alpha = 0.001;         // Probability of false failure
        Frequency frequency = new Frequency();
        for (int i = 0; i < sampleSize; i++) {
            long value = randomData.nextPoisson(mean);
            if (value > maxObservedValue) {
                maxObservedValue = value;
            }
            frequency.addValue(value);
        }

        /*
         *  Set up bins for chi-square test.
         *  Ensure expected counts are all at least minExpectedCount.
         *  Start with upper and lower tail bins.
         *  Lower bin = [0, lower); Upper bin = [upper, +inf).
         */
        PoissonDistribution poissonDistribution = new PoissonDistribution(mean);
        int lower = 1;
        while (poissonDistribution.cumulativeProbability(lower - 1) * sampleSize < minExpectedCount) {
            lower++;
        }
        int upper = (int) (5 * mean);  // Even for mean = 1, not much mass beyond 5
        while ((1 - poissonDistribution.cumulativeProbability(upper - 1)) * sampleSize < minExpectedCount) {
            upper--;
        }

        // Set bin width for interior bins.  For poisson, only need to look at end bins.
        int binWidth = 0;
        boolean widthSufficient = false;
        double lowerBinMass = 0;
        double upperBinMass = 0;
        while (!widthSufficient) {
            binWidth++;
            lowerBinMass = poissonDistribution.cumulativeProbability(lower - 1, lower + binWidth - 1);
            upperBinMass = poissonDistribution.cumulativeProbability(upper - binWidth - 1, upper - 1);
            widthSufficient = FastMath.min(lowerBinMass, upperBinMass) * sampleSize >= minExpectedCount;
        }

        /*
         *  Determine interior bin bounds.  Bins are
         *  [1, lower = binBounds[0]), [lower, binBounds[1]), [binBounds[1], binBounds[2]), ... ,
         *    [binBounds[binCount - 2], upper = binBounds[binCount - 1]), [upper, +inf)
         *
         */
        List<Integer> binBounds = new ArrayList<Integer>();
        binBounds.add(lower);
        int bound = lower + binWidth;
        while (bound < upper - binWidth) {
            binBounds.add(bound);
            bound += binWidth;
        }
        binBounds.add(upper); // The size of bin [binBounds[binCount - 2], upper) satisfies binWidth <= size < 2*binWidth.

        // Compute observed and expected bin counts
        final int binCount = binBounds.size() + 1;
        long[] observed = new long[binCount];
        double[] expected = new double[binCount];

        // Bottom bin
        observed[0] = 0;
        for (int i = 0; i < lower; i++) {
            observed[0] += frequency.getCount(i);
        }
        expected[0] = poissonDistribution.cumulativeProbability(lower - 1) * sampleSize;

        // Top bin
        observed[binCount - 1] = 0;
        for (int i = upper; i <= maxObservedValue; i++) {
            observed[binCount - 1] += frequency.getCount(i);
        }
        expected[binCount - 1] = (1 - poissonDistribution.cumulativeProbability(upper - 1)) * sampleSize;

        // Interior bins
        for (int i = 1; i < binCount - 1; i++) {
            observed[i] = 0;
            for (int j = binBounds.get(i - 1); j < binBounds.get(i); j++) {
                observed[i] += frequency.getCount(j);
            } // Expected count is (mass in [binBounds[i-1], binBounds[i])) * sampleSize
            expected[i] = (poissonDistribution.cumulativeProbability(binBounds.get(i) - 1) -
                poissonDistribution.cumulativeProbability(binBounds.get(i - 1) -1)) * sampleSize;
        }

        // Use chisquare test to verify that generated values are poisson(mean)-distributed
        ChiSquareTest chiSquareTest = new ChiSquareTest();
            // Fail if we can reject null hypothesis that distributions are the same
        if (chiSquareTest.chiSquareTest(expected, observed, alpha)) {
            StringBuilder msgBuffer = new StringBuilder();
            DecimalFormat df = new DecimalFormat("#.##");
            msgBuffer.append("Chisquare test failed for mean = ");
            msgBuffer.append(mean);
            msgBuffer.append(" p-value = ");
            msgBuffer.append(chiSquareTest.chiSquareTest(expected, observed));
            msgBuffer.append(" chisquare statistic = ");
            msgBuffer.append(chiSquareTest.chiSquare(expected, observed));
            msgBuffer.append(". \n");
            msgBuffer.append("bin\t\texpected\tobserved\n");
            for (int i = 0; i < expected.length; i++) {
                msgBuffer.append("[");
                msgBuffer.append(i == 0 ? 1: binBounds.get(i - 1));
                msgBuffer.append(",");
                msgBuffer.append(i == binBounds.size() ? "inf": binBounds.get(i));
                msgBuffer.append(")");
                msgBuffer.append("\t\t");
                msgBuffer.append(df.format(expected[i]));
                msgBuffer.append("\t\t");
                msgBuffer.append(observed[i]);
                msgBuffer.append("\n");
            }
            msgBuffer.append("This test can fail randomly due to sampling error with probability ");
            msgBuffer.append(alpha);
            msgBuffer.append(".");
            Assert.fail(msgBuffer.toString());
        }
    }

    /** test dispersion and failure modes for nextHex() */
    @Test
    public void testNextHex() {
    }

    /** test dispersion and failure modes for nextHex() */
    @Test
    @Retry(3)
    public void testNextSecureHex() {
    }

    @Test
    public void testNextUniformIAE() {
    }
    
    @Test
    public void testNextUniformUniformPositiveBounds() {
    }
    
    @Test
    public void testNextUniformUniformNegativeToPositiveBounds() {
    }
    
    @Test
    public void testNextUniformUniformNegaiveBounds() {
    }
    
    @Test
    public void testNextUniformUniformMaximalInterval() {
    }
    
    private void checkNextUniformUniform(double min, double max) {
        // Set up bin bounds - min, binBound[0], ..., binBound[binCount-2], max
        final int binCount = 5;
        final double binSize = max / binCount - min/binCount; // Prevent overflow in extreme value case
        final double[] binBounds = new double[binCount - 1];
        binBounds[0] = min + binSize;
        for (int i = 1; i < binCount - 1; i++) {
            binBounds[i] = binBounds[i - 1] + binSize;  // + instead of * to avoid overflow in extreme case
        }
        
        final Frequency freq = new Frequency();
        for (int i = 0; i < smallSampleSize; i++) {
            final double value = randomData.nextUniform(min, max);
            Assert.assertTrue("nextUniform range", (value > min) && (value < max));
            // Find bin
            int j = 0;
            while (j < binCount - 1 && value > binBounds[j]) {
                j++;
            }
            freq.addValue(j);
        }
       
        final long[] observed = new long[binCount];
        for (int i = 0; i < binCount; i++) {
            observed[i] = freq.getCount(i);
        }
        final double[] expected = new double[binCount];
        for (int i = 0; i < binCount; i++) {
            expected[i] = 1d / binCount;
        }
        
        TestUtils.assertChiSquareAccept(expected, observed, 0.01);
    }

    /** test exclusive endpoints of nextUniform **/
    @Test
    public void testNextUniformExclusiveEndpoints() {
    }

    /** test failure modes and distribution of nextGaussian() */
    @Test
    public void testNextGaussian() {
    }

    /** test failure modes and distribution of nextExponential() */
    @Test
    public void testNextExponential() {
    }

    /** test reseeding, algorithm/provider games */
    @Test
    public void testConfig() {
    }

    /** tests for nextSample() sampling from Collection */
    @Test
    public void testNextSample() {
    }

    @SuppressWarnings("unchecked")
    private int findSample(Object[] u, Object[] samp) {
        for (int i = 0; i < u.length; i++) {
            HashSet<Object> set = (HashSet<Object>) u[i];
            HashSet<Object> sampSet = new HashSet<Object>();
            for (int j = 0; j < samp.length; j++) {
                sampSet.add(samp[j]);
            }
            if (set.equals(sampSet)) {
                return i;
            }
        }
        Assert.fail("sample not found:{" + samp[0] + "," + samp[1] + "}");
        return -1;
    }

    /** tests for nextPermutation */
    @Test
    public void testNextPermutation() {
    }

    // Disable until we have equals
    //public void testSerial() {
    //    Assert.assertEquals(randomData, TestUtils.serializeAndRecover(randomData));
    //}

    private int findPerm(int[][] p, int[] samp) {
        for (int i = 0; i < p.length; i++) {
            boolean good = true;
            for (int j = 0; j < samp.length; j++) {
                if (samp[j] != p[i][j]) {
                    good = false;
                }
            }
            if (good) {
                return i;
            }
        }
        Assert.fail("permutation not found");
        return -1;
    }

    @Test
    public void testNextInversionDeviate() {
    }

    @Test
    public void testNextBeta() {
    }

    @Test
    public void testNextCauchy() {
    }

    @Test
    public void testNextChiSquare() {
    }

    @Test
    public void testNextF() {
    }

    @Test
    public void testNextGamma() {
    }

    @Test
    public void testNextT() {
    }

    @Test
    public void testNextWeibull() {
    }

    @Test
    public void testNextBinomial() {
    }

    @Test
    public void testNextHypergeometric() {
    }

    @Test
    public void testNextPascal() {
    }

    @Test
    public void testNextZipf() {
    }

    @Test
    /**
     * MATH-720
     */
    public void testReseed() {
    }

}