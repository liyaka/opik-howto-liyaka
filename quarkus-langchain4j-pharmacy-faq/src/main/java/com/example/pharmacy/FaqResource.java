package com.example.pharmacy;

import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

import java.util.Map;

@Path("/ask")
public class FaqResource {

    @Inject
    PharmacyAssistant assistant;

    @Inject
    Tracer tracer;

    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String ask(@QueryParam("q") String question) {
        // Root span of every trace. Its "input" and "output" attributes become the trace's
        // Input and Output columns in Opik (the HTTP server span is switched off in
        // application.properties, so there is no HTTP noise in those columns).
        Span span = tracer.spanBuilder("pharmacy_faq_ask").startSpan();
        try (Scope ignored = span.makeCurrent()) {
            span.setAttribute(AttributeKey.stringKey("input"), Json.of(Map.of("question", question)));
            String answer = assistant.answer(question);
            span.setAttribute(AttributeKey.stringKey("output"), Json.of(Map.of("answer", answer)));
            return answer;
        } catch (RuntimeException e) {
            span.recordException(e);
            span.setStatus(StatusCode.ERROR);
            throw e;
        } finally {
            span.end();
        }
    }
}
