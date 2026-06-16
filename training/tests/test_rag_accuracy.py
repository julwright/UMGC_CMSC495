import unittest
import chromadb
from chromadb.utils import embedding_functions

class TestRagAccuracy(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """
        Runs once before all other tests. Initializes ChromaDB client.
        """
        
        cls.db_path = "../chroma_db"
        cls.collection_name = "wp_vulnerabilities"
        
        cls.client = chromadb.PersistentClient(path=cls.db_path)
        
        cls.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        try:
            cls.collection = cls.client.get_collection(
                name=cls.collection_name,
                embedding_function=cls.embedding_func
            )
        except Exception as e:
            raise RuntimeError(
                f"Could not load collection '{cls.collection_name}' from {cls.db_path}. "
            ) from e
            
    def test_exact_slug_retrieval_accuracy(self):
        """
        Given a plugin slug with multiple associated CVEs
        When fetching records via metadata filtering
        Then the database must return exactly two distinct records matching both expected CVE IDs.
        """
        
        target_slug = "molie-instructure-canvas-linking-tool"
        expected_cves = {"CVE-2021-25006", "CVE-2021-25007"}
        
        # fetch all entries for plugin
        results = self.collection.get(
            where={"slug": target_slug}
        )
        
        # assert payload structure is valid.
        self.assertIsNotNone(results, "Query returned a None result payload.")
        self.assertIn("metadatas", results, "Payload missing 'metadatas' field.")
        self.assertIn("documents", results, "Payload missing 'documents' field.")
        
        retrieved_metadatas = results["metadatas"]
        retrieved_documents = results["documents"]
        
        # assert that both records were successfully fetched
        self.assertEqual(
            len(retrieved_metadatas), 
            2, 
            f"Expected exactly 2 CVEs for {target_slug}, but found {len(retrieved_metadatas)}."
        )
        
        # extract the cve ids from retrieved metadata entries.
        retrieved_cve_ids = {meta["cve_id"] for meta in retrieved_metadatas}
        
        # verify both target CVEs exists in the returned set
        self.setContainsSubset(
            expected_cves, 
            retrieved_cve_ids, 
            f"Missing expected CVEs. Expected: {expected_cves}, Found: {retrieved_cve_ids}"
        )

    def test_multi_cve_document_content_integrity(self):
        """
        Given the retrieved documents for a multi-CVE plugin
        When parsing the text contents of the records
        Then ensure both unique vulnerability descriptions (XSS and SQL injection) are present.
        """
        
        target_slug = "molie-instructure-canvas-linking-tool"
        
        results = self.collection.get(
            where={"slug": target_slug}
        )
        
        combined_document_text = "\n".join(results["documents"])
        
        # assert that the unique properties of CVE-2021-25006 exist in the context chunk
        self.assertIn(
            "Reflected Cross-Site Scripting",
            combined_document_text,
            "Vulnerability context for CVE-2021-25006 (XSS) is missing from the retrieved payload."
        )
    
        # Assert that the unique properties of CVE-2021-25007 exist in the context chunk
        self.assertIn(
            "SQL Injection", 
            combined_document_text, 
            "Vulnerability context for CVE-2021-25007 (SQL Injection) is missing from the retrieved payload."
        )

    def test_multi_cve_score_extraction(self):
        """
        GIVEN the metadata values returned for a multi-CVE plugin
        WHEN assessing severity levels
        THEN check that individual scores are preserved cleanly as unique floating-point strings.
        """
        target_slug = "molie-instructure-canvas-linking-tool"
        expected_scores = {6.1, 8.8}
        
        results = self.collection.get(
            where={"slug": target_slug}
        )
        
        retrieved_scores = {float(meta["score"]) for meta in results["metadatas"]}
        
        self.assertEqual(
            expected_scores, 
            retrieved_scores, 
            f"Severity scores do not match. Expected: {expected_scores}, Found: {retrieved_scores}"
        )
        
    def setContainsSubset(self, expected_set, actual_set, msg=None):
        """Helper method to check if expected set matches the actual set."""
        if not expected_set.issubset(actual_set):
            raise self.failureException(msg or f"{expected_set} is not a subset of {actual_set}")

if __name__ == "__main__":
    unittest.main(verbosity=2)