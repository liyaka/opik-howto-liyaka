package com.example.pharmacy;

import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.rag.DefaultRetrievalAugmentor;
import dev.langchain4j.rag.RetrievalAugmentor;
import dev.langchain4j.rag.content.retriever.EmbeddingStoreContentRetriever;
import dev.langchain4j.store.embedding.EmbeddingStore;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.util.function.Supplier;

@ApplicationScoped
public class LeafletRetrievalAugmentor implements Supplier<RetrievalAugmentor> {

    private final RetrievalAugmentor augmentor;

    @Inject
    public LeafletRetrievalAugmentor(EmbeddingStore<TextSegment> store, EmbeddingModel embeddingModel) {
        var retriever = EmbeddingStoreContentRetriever.builder()
                .embeddingStore(store)
                .embeddingModel(embeddingModel)
                .maxResults(3)
                .minScore(0.3)
                .build();
        this.augmentor = DefaultRetrievalAugmentor.builder().contentRetriever(retriever).build();
    }

    @Override
    public RetrievalAugmentor get() {
        return augmentor;
    }
}
