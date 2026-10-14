package com.example.pharmacy;

import dev.langchain4j.data.document.Metadata;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.inmemory.InMemoryEmbeddingStore;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.enterprise.inject.Produces;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

@ApplicationScoped
public class LeafletIndex {

    private static final Logger LOG = Logger.getLogger(LeafletIndex.class);

    @Inject
    EmbeddingModel embeddingModel;

    @ConfigProperty(name = "pharmacy.docs-dir", defaultValue = "docs")
    String docsDir;

    private final InMemoryEmbeddingStore<TextSegment> store = new InMemoryEmbeddingStore<>();

    @Produces
    @ApplicationScoped
    EmbeddingStore<TextSegment> embeddingStore() {
        return store;
    }

    void onStart(@Observes StartupEvent event) throws IOException {
        List<TextSegment> segments = new ArrayList<>();
        try (Stream<Path> files = Files.list(Path.of(docsDir))) {
            for (Path file : files.filter(f -> f.toString().endsWith(".md")).sorted().toList()) {
                segments.addAll(split(file));
            }
        }
        List<Embedding> embeddings = embeddingModel.embedAll(segments).content();
        store.addAll(embeddings, segments);
        LOG.infof("Indexed %d leaflet sections from %s", segments.size(), docsDir);
    }

    /** One segment per "## " section, each prefixed with the leaflet title so it stands alone. */
    static List<TextSegment> split(Path file) throws IOException {
        String[] lines = Files.readString(file).split("\n");
        String title = lines[0].replaceFirst("^#\\s*", "").trim();
        List<TextSegment> out = new ArrayList<>();
        String heading = null;
        StringBuilder body = new StringBuilder();
        for (int i = 1; i < lines.length; i++) {
            if (lines[i].startsWith("## ")) {
                flush(out, file, title, heading, body);
                heading = lines[i].substring(3).trim();
                body.setLength(0);
            } else {
                body.append(lines[i]).append('\n');
            }
        }
        flush(out, file, title, heading, body);
        return out;
    }

    private static void flush(List<TextSegment> out, Path file, String title, String heading, StringBuilder body) {
        String text = body.toString().trim();
        if (heading == null || text.isEmpty()) {
            return;
        }
        Metadata metadata = new Metadata().put("source", file.getFileName().toString()).put("section", heading);
        out.add(TextSegment.from(title + " - " + heading + ": " + text, metadata));
    }
}
