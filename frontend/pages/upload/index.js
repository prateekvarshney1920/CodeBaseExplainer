import Head from "next/head";
import { useState, useCallback } from "react";
import InputPanel from "../../components/InputPanel";
import FileTree from "../../components/FileTree";
import DependencyGraph from "../../components/DependencyGraph";
import ExplanationPanel from "../../components/ExplanationPanel";
import PromptEditor from "../../components/PromptEditor";
import { analyzeGithub, analyzeUpload, explainFile } from "../../lib/api";

export default function Home() {
  // Analysis state (Logic Unchanged)
  const [analysisData, setAnalysisData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isExplaining, setIsExplaining] = useState(false);
  const [currentSummary, setCurrentSummary] = useState("");
  const [error, setError] = useState("");

  // Handle analysis (GitHub or Upload - Logic Unchanged)
  const handleAnalyze = useCallback(async (input) => {
    setIsLoading(true);
    setLoadingStep(0);
    setError("");
    setAnalysisData(null);
    setSelectedFile(null);
    setCurrentSummary("");

    const stepInterval = setInterval(() => {
      setLoadingStep((prev) => (prev < 4 ? prev + 1 : prev));
    }, 2000);

    try {
      let result;
      if (input.type === "github") {
        result = await analyzeGithub(input.url);
      } else {
        result = await analyzeUpload(input.file);
      }
      setAnalysisData(result);
      setLoadingStep(5);
    } catch (err) {
      setError(err.message);
    } finally {
      clearInterval(stepInterval);
      setIsLoading(false);
    }
  }, []);

  // Handle file selection (Logic Unchanged)
  const handleFileClick = useCallback(
    (filepath) => {
      setSelectedFile(filepath);
      if (analysisData?.summaries?.[filepath]) {
        setCurrentSummary(analysisData.summaries[filepath]);
      } else {
        setCurrentSummary("");
      }
    },
    [analysisData]
  );

  // Handle "explain simpler" (Logic Unchanged)
  const handleExplainSimple = useCallback(
    async (filepath) => {
      if (!analysisData?.files?.[filepath]) return;
      setIsExplaining(true);
      try {
        const result = await explainFile(
          filepath,
          analysisData.files[filepath],
          true
        );
        setCurrentSummary(result.explanation);
      } catch (err) {
        setCurrentSummary(`Error: ${err.message}`);
      } finally {
        setIsExplaining(false);
      }
    },
    [analysisData]
  );

  // Build parsed files data (Logic Unchanged)
  const parsedFiles = analysisData?.graph?.nodes
    ? Object.fromEntries(
        analysisData.graph.nodes.map((n) => [
          n.id,
          {
            language: n.data?.language || "unknown",
            imports: n.data?.imports || [],
            exports: n.data?.exports || [],
            declarations: n.data?.declarations || [],
          },
        ])
      )
    : {};

  const selectedFileData = selectedFile ? parsedFiles[selectedFile] : null;

  return (
    <>
      <Head>
        <title>CodeBase Explainer — AI-Powered Code Analysis</title>
        <meta name="description" content="AI-powered code analysis" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="app-container">
        {/* IMPROVED HEADER UI */}
        <header className="app-header">
          <div className="logo">
            <div className="logo-icon">🧠</div>
            <h1>CodeBase <span>Explainer</span></h1>
          </div>
          <div className="header-actions">
             <PromptEditor />
          </div>
        </header>

        <main className="main-content">
          {/* LEFT: Explorer Panel */}
          <div className="left-panel">
            <div className="panel-inner">
              <InputPanel
                onAnalyze={handleAnalyze}
                isLoading={isLoading}
                loadingStep={loadingStep}
              />
              {analysisData && (
                <div className="tree-container">
                  <FileTree
                    parsedFiles={parsedFiles}
                    entryPoints={analysisData.entry_points || []}
                    cycles={analysisData.cycles || []}
                    onFileClick={handleFileClick}
                    selectedFile={selectedFile}
                  />
                </div>
              )}
            </div>
          </div>

          {/* CENTER: Visualization Graph */}
          <div className="center-panel">
            <div className="graph-wrapper">
              <DependencyGraph
                graphData={analysisData?.graph}
                onNodeClick={handleFileClick}
                selectedNode={selectedFile}
                entryPoints={analysisData?.entry_points || []}
                cycles={analysisData?.cycles || []}
              />
            </div>
            {error && <div className="error-toast">{error}</div>}
          </div>

          {/* RIGHT: Analysis Panel */}
          <div className="right-panel">
            <ExplanationPanel
              selectedFile={selectedFile}
              fileData={selectedFileData}
              summary={currentSummary}
              architectureOverview={analysisData?.architecture_overview || ""}
              onExplainSimple={handleExplainSimple}
              isExplaining={isExplaining}
            />
          </div>
        </main>
      </div>
    </>
  );
}