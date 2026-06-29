# Uncleaned vs. Cleaned Data Study Findings

## Model Usage
* **Uncleaned Study:** `gemma 4 31b`
* **Cleaned PDFs Study:** `gemma 4 26b`

## Key Findings

1. **Hallucinations & Misclassifications in Uncleaned Data:**
   * There were many hallucinations present when processing the uncleaned documents.
   * A significant portion of the uncleaned documents were incorrectly recognized and classified as **"Allocation Order"**.

2. **Model Behavior on Clear Documents:**
   * When documents were clear, the larger model (`gemma 4 31b`) was remarkably capable. It could even override strict instructions to determine what it thought was the correct letter, and in many of these cases, its overriding deduction was actually correct.

3. **Model Behavior on Unclear Documents:**
   * On the flip side, when the document was not clear, the intelligence of the larger model did not prevent it from failing; the hallucinations were just as bad.

4. **Quantitative Observations (From the Comparison Script):**
   * **Total Changes Detected:**
     * **Summary Changes:** 209 instances where the summary was altered or improved.
     * **Residents Changes:** 93 instances where the extracted residents differed.
     * **Classification Changes:** 55 instances where the document category changed.
   * **Most Frequent Categorical Shifts (Uncleaned -> Cleaned):**
     * *Allocation Order* -> *Miscellaneous Letters* (7 times)
     * *Personal Identification* -> *Miscellaneous Letters* (7 times)
     * *Allocation Order* -> *Maintenance Records* (7 times)
     * *Inspection and Pictures* -> *Maintenance Records* (7 times)
     * *Miscellaneous Letters* -> *Property Modifications* (6 times)
   * **Resident Extraction Quality:** 
     * The uncleaned documents frequently resulted in empty or wildly hallucinated resident names, which were subsequently fixed or marked correctly in the cleaned version.

## Conclusion
While a more powerful model (`gemma 4 31b`) provides impressive reasoning capabilities—even correcting bad instructions on clear documents—it is fundamentally bottlenecked by the quality of the OCR and document preprocessing. Unclear documents inevitably lead to severe hallucinations regardless of the model's size, highlighting the critical importance of utilizing cleaned data (`gemma 4 26b` was able to achieve better categorizations due to the data quality).
