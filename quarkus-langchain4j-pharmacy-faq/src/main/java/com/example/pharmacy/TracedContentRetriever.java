package com.example.pharmacy;

import dev.langchain4j.rag.content.Content;
import dev.langchain4j.rag.content.ContentMetadata;
import dev.langchain4j.rag.content.retriever.ContentRetriever;
import dev.langchain4j.rag.query.Query;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;

import java.util.List;
import java.util.Map;

/**
 * Wraps the real retriever so the retrieval step becomes its own span. Quarkus LangChain4j
 * emits spans for the AI-service call and the chat model, but nothing for the vector search.
 */
public class TracedContentRetriever implements ContentRetriever {

    private final ContentRetriever delegate;
    private final Tracer tracer;
    private final int topK;

    public TracedContentRetriever(ContentRetriever delegate, Tracer tracer, int topK) {
        this.delegate = delegate;
        this.tracer = tracer;
        this.topK = topK;
    }

    @Override
    public List<Content> retrieve(Query query) {
        Span span = tracer.spanBuilder("retrieve_leaflet_sections").startSpan();
        try (Scope ignored = span.makeCurrent()) {
            // gen_ai.tool.call.* are attributes Opik maps to a tool span's input and output,
            // so the question and the retrieved chunks show up as that span's Input and Output tabs.
            span.setAttribute("gen_ai.tool.name", "leaflet_retrieval");
            span.setAttribute(AttributeKey.stringKey("gen_ai.tool.call.arguments"),
                    Json.of(Map.of("query", query.text(), "top_k", topK)));
            List<Content> contents = delegate.retrieve(query);
            span.setAttribute(AttributeKey.stringKey("gen_ai.tool.call.result"),
                    Json.of(Map.of("documents", contents.stream().map(TracedContentRetriever::describe).toList())));
            return contents;
        } catch (RuntimeException e) {
            span.recordException(e);
            span.setStatus(StatusCode.ERROR);
            throw e;
        } finally {
            span.end();
        }
    }

    private static Map<String, Object> describe(Content content) {
        var segment = content.textSegment();
        return Map.of(
                "source", String.valueOf(segment.metadata().getString("source")),
                "section", String.valueOf(segment.metadata().getString("section")),
                "score", String.valueOf(content.metadata().get(ContentMetadata.SCORE)),
                "text", segment.text());
    }
}
