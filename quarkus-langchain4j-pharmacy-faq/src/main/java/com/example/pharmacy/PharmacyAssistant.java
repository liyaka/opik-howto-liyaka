package com.example.pharmacy;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import io.quarkiverse.langchain4j.RegisterAiService;
import jakarta.enterprise.context.ApplicationScoped;

@RegisterAiService(retrievalAugmentor = LeafletRetrievalAugmentor.class)
@ApplicationScoped
public interface PharmacyAssistant {

    @SystemMessage("""
            You are the medication-information assistant of Harbourlight Pharmacy.
            Answer only from the leaflet excerpts you are given, in two to four plain sentences.
            If the excerpts do not cover the question, say you do not have that information.
            Never diagnose, never recommend a dose that is not in the excerpts, and never tell
            anyone to start, stop or change a medicine.
            End every answer with this sentence: "This is general leaflet information, so please
            ask your pharmacist or prescriber about your own situation."
            """)
    String answer(@UserMessage String question);
}
