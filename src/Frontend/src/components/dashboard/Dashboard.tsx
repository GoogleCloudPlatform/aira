'use client';

import React, { useState, useEffect, useMemo } from "react";
import { useTranslations } from "next-intl";
import { 
    TrendingUp, Users, BookOpen, Award, Search, Filter, 
    CheckCircle, XCircle, ChevronRight, Calendar, RefreshCw,
    ArrowUpDown, BookMarked, AlertCircle, Star, Sparkles
} from "lucide-react";
import { getDashboardResults } from "@/services/user";
import Loading from "@/components/loading/Loading";
import { getFormattedDate } from "@/utils";
import { useParams } from "next/navigation";

interface BigQueryRow {
  school_uuid: string;
  school_name: string;
  school_city: string;
  school_state: string;
  school_region: string | null;
  class_uuid: string;
  class_name: string;
  class_grade: string;
  student_uuid: string;
  student_customer_id: string | null;
  student_name: string;
  exam_uuid: string;
  exam_name: string;
  exam_grade: string;
  exam_start_date: string;
  exam_end_date: string;
  question_uuid: string;
  question_words: string[];
  question_amount_words: number;
  response_words: string[];
  response_amount_hits: number;
  response_timestamp: string;
  user_rating: string | null;
}

interface StudentAggregation {
  uuid: string;
  name: string;
  className: string;
  grade: string;
  totalQuestions: number;
  totalHits: number;
  accuracy: number;
  latestRating: string;
  examsTaken: Set<string>;
  attempts: Array<{
    examName: string;
    timestamp: string;
    hits: number;
    totalWords: number;
    accuracy: number;
    rating: string;
    wordsList: string[];
    responseWords: string[];
  }>;
}

// Multi-language localization dictionary helper for dashboard specific strings
const DASHBOARD_LANG = {
    "en-US": {
        portalTitle: "Proficiency insights provided by Gemini",
        dashboardTitle: "Reports Dashboard",
        dashboardSubtitle: "Track and assess oral reading fluency, accuracy, and student progression metrics in real-time.",
        refreshData: "Refresh Data",
        refreshing: "Refreshing...",
        classAccuracy: "Class Accuracy",
        targetAccuracy: "Target > 70%",
        activeStudents: "Active Students",
        inClasses: "In {n} Classes",
        predominantLevel: "Predominant Level",
        mostCommonStatus: "Most common status",
        evaluationsTaken: "Evaluations Taken",
        aggregatedBigQuery: "Aggregated from BigQuery",
        filterStudents: "Filter Students:",
        searchPlaceholder: "Search student...",
        allClasses: "All Classes ({n})",
        allExams: "All Exams ({n})",
        allReadingLevels: "All Reading Levels ({n})",
        clearFilters: "Clear Filters",
        levelsDistribution: "Reading Levels Distribution",
        levelsDistributionSub: "Interactive distribution based on student ratings. Click a level to filter.",
        noLevelsData: "No reading level data available.",
        studentPerformances: "Student Performances",
        performancesSub: "Detailed metrics computed from BigQuery.",
        showingStudents: "Showing {n} of {m} Students",
        noStudentsMatched: "No students match the selected filters.",
        studentHeader: "Student",
        classHeader: "Class / Grade",
        examsHeader: "Exams",
        accuracyHeader: "Accuracy",
        levelHeader: "Reading Level",
        actionsHeader: "Actions",
        viewDetails: "View Details",
        hideDetails: "Hide Details",
        interventionNeeded: "Intervention Needed",
        interventionSub: "Students with < 50% oral reading accuracy.",
        allStudentsFluency: "All students are reading with target accuracy!",
        examsAssessment: "Exams Assessment",
        examsAssessmentSub: "Comparing average accuracy scores by exam.",
        noExamsData: "No exam metrics available.",
        attemptsTimeline: "Reading fluencies attempts timeline",
        totalAttempts: "total attempts",
        totalResponses: "total responses",
        avgAccuracy: "Average Accuracy",
        accuracyLabel: "Accuracy:",
        fluencyLabel: "Fluency rating:",
        readingResults: "Audio-to-Text Transcribed Reading Results:",
        correctWords: "Correct words",
        missedWords: "Missed",
        avgShort: "Avg"
    },
    "pt-BR": {
        portalTitle: "Insights de proficiência fornecidos pelo Gemini",
        dashboardTitle: "Painel de Relatórios",
        dashboardSubtitle: "Acompanhe e avalie a fluência de leitura oral, precisão e métricas de progressão dos alunos em tempo real.",
        refreshData: "Atualizar Dados",
        refreshing: "Atualizando...",
        classAccuracy: "Precisão da Turma",
        targetAccuracy: "Meta > 70%",
        activeStudents: "Alunos Ativos",
        inClasses: "Em {n} Turmas",
        predominantLevel: "Nível Predominante",
        mostCommonStatus: "Status mais comum",
        evaluationsTaken: "Avaliações Realizadas",
        aggregatedBigQuery: "Agregado do BigQuery",
        filterStudents: "Filtrar Alunos:",
        searchPlaceholder: "Buscar aluno...",
        allClasses: "Todas as Turmas ({n})",
        allExams: "Todas as Avaliações ({n})",
        allReadingLevels: "Todos os Níveis de Leitura ({n})",
        clearFilters: "Limpar Filtros",
        levelsDistribution: "Distribuição dos Níveis de Leitura",
        levelsDistributionSub: "Distribuição interativa baseada nas classificações dos alunos. Clique em um nível para filtrar.",
        noLevelsData: "Nenhum dado de nível de leitura disponível.",
        studentPerformances: "Desempenho dos Alunos",
        performancesSub: "Métricas detalhadas calculadas a partir do BigQuery.",
        showingStudents: "Mostrando {n} de {m} Alunos",
        noStudentsMatched: "Nenhum aluno corresponde aos filtros selecionados.",
        studentHeader: "Aluno",
        classHeader: "Turma / Série",
        examsHeader: "Avaliações",
        accuracyHeader: "Precisão",
        levelHeader: "Nível de Leitura",
        actionsHeader: "Ações",
        viewDetails: "Ver Detalhes",
        hideDetails: "Ocultar Detalhes",
        interventionNeeded: "Intervenção Necessária",
        interventionSub: "Alunos com menos de 50% de precisão de leitura oral.",
        allStudentsFluency: "Todos os alunos estão lendo com a precisão desejada!",
        examsAssessment: "Avaliação das Provas",
        examsAssessmentSub: "Comparando as pontuações médias de precisão por avaliação.",
        noExamsData: "Nenhuma métrica de avaliação disponível.",
        attemptsTimeline: "Linha do tempo de tentativas de fluência de leitura",
        totalAttempts: "tentativas no total",
        totalResponses: "respostas no total",
        avgAccuracy: "Precisão Média",
        accuracyLabel: "Precisão:",
        fluencyLabel: "Classificação de fluência:",
        readingResults: "Resultados da Leitura Transcrita de Áudio para Texto:",
        correctWords: "Palavras corretas",
        missedWords: "Missed",
        avgShort: "Méd"
    },
    "es-ES": {
        portalTitle: "Información de competencia proporcionada por Gemini",
        dashboardTitle: "Panel de Informes",
        dashboardSubtitle: "Siga y evalúe la fluidez de lectura oral, la precisión y las métricas de progresión de los estudiantes en tiempo real.",
        refreshData: "Actualizar Datos",
        refreshing: "Actualizando...",
        classAccuracy: "Precisión del Grupo",
        targetAccuracy: "Meta > 70%",
        activeStudents: "Estudiantes Activos",
        inClasses: "En {n} Grupos",
        predominantLevel: "Nivel Predominante",
        mostCommonStatus: "Estado más común",
        evaluationsTaken: "Evaluaciones Realizadas",
        aggregatedBigQuery: "Agregado de BigQuery",
        filterStudents: "Filtrar Estudiantes:",
        searchPlaceholder: "Buscar estudiante...",
        allClasses: "Todos los Grupos ({n})",
        allExams: "Todas las Evaluaciones ({n})",
        allReadingLevels: "Todos los Niveles de Lectura ({n})",
        clearFilters: "Limpiar Filtros",
        levelsDistribution: "Distribución de Niveles de Lectura",
        levelsDistributionSub: "Distribución interactiva basada en las calificaciones de los estudiantes. Haga clic en un nivel para filtrar.",
        noLevelsData: "No hay datos de nivel de lectura disponibles.",
        studentPerformances: "Desempeño de los Estudiantes",
        performancesSub: "Métricas detalladas calculadas a partir de BigQuery.",
        showingStudents: "Mostrando {n} de {m} Estudiantes",
        noStudentsMatched: "Ningún estudiante coincide con los filtros seleccionados.",
        studentHeader: "Estudiante",
        classHeader: "Grupo / Grado",
        examsHeader: "Evaluaciones",
        accuracyHeader: "Precisión",
        levelHeader: "Nivel de Lectura",
        actionsHeader: "Acciones",
        viewDetails: "Ver Detalles",
        hideDetails: "Ocultar Detalles",
        interventionNeeded: "Intervención Necesaria",
        interventionSub: "Estudiantes con menos del 50% de precisión de lectura oral.",
        allStudentsFluency: "¡Todos los estudiantes leen con la precisión objetiva!",
        examsAssessment: "Evaluación de las Pruebas",
        examsAssessmentSub: "Comparando las puntuaciones de precisión promedio por evaluación.",
        noExamsData: "No hay métricas de evaluación disponibles.",
        attemptsTimeline: "Cronología de intentos de fluidez de lectura",
        totalAttempts: "intentos totales",
        totalResponses: "respuestas totales",
        avgAccuracy: "Precisión Promedio",
        accuracyLabel: "Precisión:",
        fluencyLabel: "Clasificación de fluidez:",
        readingResults: "Resultados de la Lectura Transcrita de Audio a Texto:",
        correctWords: "Palabras correctas",
        missedWords: "Missed",
        avgShort: "Prom"
    }
};

export const Dashboard: React.FC = () => {
    const t = useTranslations();
    const { locale } = useParams();
    
    // Select proper dictionary based on locale, defaulting to en-US
    const dl = useMemo(() => {
        const activeLocale = (locale as string) || "en-US";
        return DASHBOARD_LANG[activeLocale as keyof typeof DASHBOARD_LANG] || DASHBOARD_LANG["en-US"];
    }, [locale]);

    const [data, setData] = useState<BigQueryRow[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [refreshing, setRefreshing] = useState<boolean>(false);
    const [searchTerm, setSearchTerm] = useState<string>("");
    const [selectedClass, setSelectedClass] = useState<string>("ALL");
    const [selectedExam, setSelectedExam] = useState<string>("ALL");
    const [selectedRating, setSelectedRating] = useState<string>("ALL");
    const [selectedStudent, setSelectedStudent] = useState<StudentAggregation | null>(null);
    const [sortField, setSortField] = useState<"name" | "accuracy" | "exams">("accuracy");
    const [sortAsc, setSortAsc] = useState<boolean>(false);

    const loadData = async () => {
        try {
            setLoading(true);
            const results = await getDashboardResults();
            setData(results || []);
        } catch (err) {
            console.error("Error loading dashboard data", err);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleRefresh = () => {
        setRefreshing(true);
        loadData();
    };

    // Aggregating student-level performance
    const studentMetrics = useMemo(() => {
        const studentsMap: Record<string, StudentAggregation> = {};

        data.forEach((row) => {
            const sId = row.student_uuid;
            if (!studentsMap[sId]) {
                studentsMap[sId] = {
                    uuid: sId,
                    name: row.student_name,
                    className: row.class_name,
                    grade: row.class_grade,
                    totalQuestions: 0,
                    totalHits: 0,
                    accuracy: 0,
                    latestRating: row.user_rating || "N/A",
                    examsTaken: new Set<string>(),
                    attempts: [],
                };
            }

            const student = studentsMap[sId];
            student.totalQuestions += row.question_amount_words;
            student.totalHits += row.response_amount_hits;
            student.examsTaken.add(row.exam_name);

            // Save attempt details
            student.attempts.push({
                examName: row.exam_name,
                timestamp: row.response_timestamp,
                hits: row.response_amount_hits,
                totalWords: row.question_amount_words,
                accuracy: row.question_amount_words > 0 ? (row.response_amount_hits / row.question_amount_words) * 100 : 0,
                rating: row.user_rating || "N/A",
                wordsList: row.question_words || [],
                responseWords: row.response_words || [],
            });
        });

        // Calculate average accuracy for each student and sort attempts by timestamp
        return Object.values(studentsMap).map((student) => {
            student.accuracy = student.totalQuestions > 0 ? (student.totalHits / student.totalQuestions) * 100 : 0;
            student.attempts.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
            if (student.attempts.length > 0) {
                student.latestRating = student.attempts[0].rating;
            }
            return student;
        });
    }, [data]);

    // Filter Options Extraction
    const classOptions = useMemo(() => {
        const classes = new Set<string>();
        data.forEach((row) => classes.add(row.class_name));
        return Array.from(classes);
    }, [data]);

    const examOptions = useMemo(() => {
        const exams = new Set<string>();
        data.forEach((row) => exams.add(row.exam_name));
        return Array.from(exams);
    }, [data]);

    const ratingOptions = useMemo(() => {
        const ratings = new Set<string>();
        studentMetrics.forEach((student) => {
            if (student.latestRating) ratings.add(student.latestRating);
        });
        return Array.from(ratings);
    }, [studentMetrics]);

    // Applying Filters
    const filteredStudents = useMemo(() => {
        return studentMetrics
            .filter((student) => {
                const matchesSearch = student.name.toLowerCase().includes(searchTerm.toLowerCase());
                const matchesClass = selectedClass === "ALL" || student.className === selectedClass;
                const matchesRating = selectedRating === "ALL" || student.latestRating === selectedRating;
                const matchesExam = selectedExam === "ALL" || Array.from(student.examsTaken).includes(selectedExam);
                return matchesSearch && matchesClass && matchesRating && matchesExam;
            })
            .sort((a, b) => {
                let comparison = 0;
                if (sortField === "name") {
                    comparison = a.name.localeCompare(b.name);
                } else if (sortField === "accuracy") {
                    comparison = a.accuracy - b.accuracy;
                } else if (sortField === "exams") {
                    comparison = a.examsTaken.size - b.examsTaken.size;
                }
                return sortAsc ? comparison : -comparison;
            });
    }, [studentMetrics, searchTerm, selectedClass, selectedRating, selectedExam, sortField, sortAsc]);

    // Class KPIs calculations
    const kpis = useMemo(() => {
        if (filteredStudents.length === 0) {
            return {
                avgAccuracy: 0,
                activeStudents: 0,
                predominantRating: "N/A",
                totalAttempts: 0,
            };
        }

        const totalAccuracy = filteredStudents.reduce((sum, s) => sum + s.accuracy, 0);
        const avgAccuracy = totalAccuracy / filteredStudents.length;

        // Predominant level calculation
        const ratingCounts: Record<string, number> = {};
        filteredStudents.forEach((s) => {
            if (s.latestRating) {
                ratingCounts[s.latestRating] = (ratingCounts[s.latestRating] || 0) + 1;
            }
        });
        let predominantRating = "N/A";
        let maxCount = 0;
        Object.entries(ratingCounts).forEach(([rating, count]) => {
            if (count > maxCount) {
                maxCount = count;
                predominantRating = rating;
            }
        });

        const totalAttempts = filteredStudents.reduce((sum, s) => sum + s.attempts.length, 0);

        return {
            avgAccuracy,
            activeStudents: filteredStudents.length,
            predominantRating,
            totalAttempts,
        };
    }, [filteredStudents]);

    // Rating Distribution data for horizontal custom bar charts
    const ratingDistribution = useMemo(() => {
        const distribution: Record<string, number> = {};
        filteredStudents.forEach((s) => {
            if (s.latestRating) {
                distribution[s.latestRating] = (distribution[s.latestRating] || 0) + 1;
            }
        });

        return Object.entries(distribution).map(([name, count]) => ({
            name,
            count,
            percentage: filteredStudents.length > 0 ? (count / filteredStudents.length) * 100 : 0,
        })).sort((a, b) => b.count - a.count);
    }, [filteredStudents]);

    // Intervention list (Students with accuracy < 50%)
    const interventionStudents = useMemo(() => {
        return filteredStudents.filter((s) => s.accuracy < 50);
    }, [filteredStudents]);

    const handleSort = (field: "name" | "accuracy" | "exams") => {
        if (sortField === field) {
            setSortAsc(!sortAsc);
        } else {
            setSortField(field);
            setSortAsc(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <Loading style="vertical" text={true} />
            </div>
        );
    }

    return (
        <div className="w-full h-full overflow-y-auto text-slate-900 dark:text-slate-100 px-4 sm:px-6 py-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <div className="flex items-center gap-2 text-primary dark:text-blue-400 mb-2 font-semibold tracking-wider uppercase text-xs">
                        <Sparkles className="w-4 h-4" />
                        {dl.portalTitle}
                    </div>
                    <h1 className="text-3xl sm:text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-500 dark:from-blue-400 dark:to-indigo-300 bg-clip-text text-transparent">
                        {t("sidebar.options.reports") || dl.dashboardTitle}
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 text-sm sm:text-base mt-1">
                        {dl.dashboardSubtitle}
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleRefresh}
                        disabled={refreshing}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm hover:bg-slate-50 dark:hover:bg-slate-750 transition duration-150"
                    >
                        <RefreshCw className={`w-4 h-4 text-slate-500 dark:text-slate-400 ${refreshing ? "animate-spin" : ""}`} />
                        {refreshing ? dl.refreshing : dl.refreshData}
                    </button>
                </div>
            </div>

            {/* KPI Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                {/* Circular Accuracy Gauge Card */}
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm flex items-center justify-between relative overflow-hidden group hover:shadow-md hover:border-blue-400 dark:hover:border-blue-600 transition-all duration-300">
                    <div className="flex flex-col">
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            {dl.classAccuracy}
                        </span>
                        <span className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                            {kpis.avgAccuracy.toFixed(1)}%
                        </span>
                        <span className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1 mt-2 font-medium">
                            <TrendingUp className="w-3.5 h-3.5" />
                            {dl.targetAccuracy}
                        </span>
                    </div>
                    <div className="relative w-16 h-16 flex items-center justify-center">
                        <svg className="w-full h-full transform -rotate-90">
                            <circle
                                cx="32"
                                cy="32"
                                r="26"
                                className="stroke-slate-150 dark:stroke-slate-700"
                                strokeWidth="4.5"
                                fill="transparent"
                            />
                            <circle
                                cx="32"
                                cy="32"
                                r="26"
                                className="stroke-blue-600 dark:stroke-blue-500"
                                strokeWidth="4.5"
                                fill="transparent"
                                strokeDasharray={2 * Math.PI * 26}
                                strokeDashoffset={2 * Math.PI * 26 * (1 - kpis.avgAccuracy / 100)}
                                strokeLinecap="round"
                            />
                        </svg>
                        <div className="absolute text-xs font-bold text-blue-600 dark:text-blue-400">
                            {dl.avgShort}
                        </div>
                    </div>
                    <div className="absolute top-0 right-0 h-1 w-full bg-gradient-to-r from-blue-500 to-indigo-500 opacity-0 group-hover:opacity-100 transition-all duration-300" />
                </div>

                {/* Active Students */}
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm flex items-center justify-between relative overflow-hidden group hover:shadow-md hover:border-indigo-400 dark:hover:border-indigo-600 transition-all duration-300">
                    <div>
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            {dl.activeStudents}
                        </span>
                        <span className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100 mt-1 block">
                            {kpis.activeStudents}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400 block mt-2">
                            {dl.inClasses.replace("{n}", classOptions.length.toString())}
                        </span>
                    </div>
                    <div className="p-3.5 bg-indigo-50 dark:bg-indigo-950/30 rounded-lg text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform duration-300">
                        <Users className="w-6 h-6" />
                    </div>
                    <div className="absolute top-0 right-0 h-1 w-full bg-gradient-to-r from-indigo-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-all duration-300" />
                </div>

                {/* Predominant Rating */}
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm flex items-center justify-between relative overflow-hidden group hover:shadow-md hover:border-emerald-400 dark:hover:border-emerald-600 transition-all duration-300">
                    <div>
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            {dl.predominantLevel}
                        </span>
                        <span className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100 mt-1.5 block truncate max-w-[180px]" title={kpis.predominantRating}>
                            {kpis.predominantRating}
                        </span>
                        <span className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1 mt-2 font-medium">
                            <Award className="w-3.5 h-3.5" />
                            {dl.mostCommonStatus}
                        </span>
                    </div>
                    <div className="p-3.5 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform duration-300">
                        <Award className="w-6 h-6" />
                    </div>
                    <div className="absolute top-0 right-0 h-1 w-full bg-gradient-to-r from-emerald-500 to-teal-500 opacity-0 group-hover:opacity-100 transition-all duration-300" />
                </div>

                {/* Evaluations Conducted */}
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-sm flex items-center justify-between relative overflow-hidden group hover:shadow-md hover:border-purple-400 dark:hover:border-purple-600 transition-all duration-300">
                    <div>
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            {dl.evaluationsTaken}
                        </span>
                        <span className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100 mt-1 block">
                            {kpis.totalAttempts}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400 block mt-2">
                            {dl.aggregatedBigQuery}
                        </span>
                    </div>
                    <div className="p-3.5 bg-purple-50 dark:bg-purple-950/30 rounded-lg text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform duration-300">
                        <BookOpen className="w-6 h-6" />
                    </div>
                    <div className="absolute top-0 right-0 h-1 w-full bg-gradient-to-r from-purple-500 to-pink-500 opacity-0 group-hover:opacity-100 transition-all duration-300" />
                </div>
            </div>

            {/* Interactive Filters Bar */}
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4 mb-8 shadow-sm flex flex-col lg:flex-row lg:items-center gap-4">
                <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-sm font-medium lg:border-r lg:border-slate-200 dark:lg:border-slate-700 lg:pr-4 shrink-0">
                    <Filter className="w-4 h-4" />
                    <span>{dl.filterStudents}</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 flex-grow">
                    {/* Search name */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                            type="text"
                            placeholder={dl.searchPlaceholder}
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none transition duration-150"
                        />
                    </div>

                    {/* Class Select */}
                    <select
                        value={selectedClass}
                        onChange={(e) => setSelectedClass(e.target.value)}
                        className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none cursor-pointer"
                    >
                        <option value="ALL">{dl.allClasses.replace("{n}", classOptions.length.toString())}</option>
                        {classOptions.map((cls) => (
                            <option key={cls} value={cls}>
                                {cls}
                            </option>
                        ))}
                    </select>

                    {/* Exam Select */}
                    <select
                        value={selectedExam}
                        onChange={(e) => setSelectedExam(e.target.value)}
                        className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none cursor-pointer"
                    >
                        <option value="ALL">{dl.allExams.replace("{n}", examOptions.length.toString())}</option>
                        {examOptions.map((ex) => (
                            <option key={ex} value={ex}>
                                {ex}
                            </option>
                        ))}
                    </select>

                    {/* Rating Select */}
                    <select
                        value={selectedRating}
                        onChange={(e) => setSelectedRating(e.target.value)}
                        className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none cursor-pointer"
                    >
                        <option value="ALL">{dl.allReadingLevels.replace("{n}", ratingOptions.length.toString())}</option>
                        {ratingOptions.map((rt) => (
                            <option key={rt} value={rt}>
                                {rt}
                            </option>
                        ))}
                    </select>
                </div>

                {(searchTerm || selectedClass !== "ALL" || selectedExam !== "ALL" || selectedRating !== "ALL") && (
                    <button
                        onClick={() => {
                            setSearchTerm("");
                            setSelectedClass("ALL");
                            setSelectedExam("ALL");
                            setSelectedRating("ALL");
                        }}
                        className="text-sm font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300 transition duration-150 shrink-0 self-end lg:self-auto"
                    >
                        {dl.clearFilters}
                    </button>
                )}
            </div>

            {/* Main Dashboard Layout */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-8">
                {/* Left Panel: Interactive Charts */}
                <div className="xl:col-span-2 flex flex-col gap-8">
                    {/* Chart 1: Reading Level Distribution */}
                    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                                    {dl.levelsDistribution}
                                </h3>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                                    {dl.levelsDistributionSub}
                                </p>
                            </div>
                        </div>

                        {ratingDistribution.length === 0 ? (
                            <div className="flex items-center justify-center h-48 text-slate-400 dark:text-slate-500 text-sm">
                                {dl.noLevelsData}
                            </div>
                        ) : (
                            <div className="flex flex-col gap-4">
                                {ratingDistribution.map((item) => {
                                    const isSelected = selectedRating === item.name;
                                    return (
                                        <div
                                            key={item.name}
                                            onClick={() => setSelectedRating(isSelected ? "ALL" : item.name)}
                                            className={`flex flex-col cursor-pointer p-2 rounded-lg transition duration-200 ${
                                                isSelected
                                                    ? "bg-blue-50 dark:bg-blue-950/35 ring-1 ring-blue-400/40"
                                                    : "hover:bg-slate-50 dark:hover:bg-slate-750"
                                            }`}
                                        >
                                            <div className="flex justify-between text-xs font-medium mb-1.5">
                                                <span className="text-slate-700 dark:text-slate-350 flex items-center gap-1.5">
                                                    <div className={`w-2.5 h-2.5 rounded-full ${
                                                        item.name.includes("4") || item.name.toLowerCase().includes("leitor")
                                                            ? "bg-green-500" 
                                                            : item.name.includes("3") 
                                                                ? "bg-blue-500" 
                                                                : "bg-amber-500"
                                                    }`} />
                                                    {item.name}
                                                </span>
                                                <span className="text-slate-500 dark:text-slate-400 font-semibold">
                                                    {item.count} student{item.count > 1 ? "s" : ""} ({item.percentage.toFixed(0)}%)
                                                </span>
                                            </div>
                                            <div className="w-full h-3 bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full transition-all duration-500 ${
                                                        item.name.includes("4") || item.name.toLowerCase().includes("leitor")
                                                            ? "bg-gradient-to-r from-green-400 to-emerald-500" 
                                                            : item.name.includes("3") 
                                                                ? "bg-gradient-to-r from-blue-400 to-indigo-500" 
                                                                : "bg-gradient-to-r from-amber-400 to-orange-500"
                                                    }`}
                                                    style={{ width: `${item.percentage}%` }}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {/* Table / List of Students */}
                    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm overflow-hidden">
                        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between flex-wrap gap-4 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-800/50">
                            <div>
                                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                                    {dl.studentPerformances}
                                </h3>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                                    {dl.performancesSub}
                                </p>
                            </div>
                            <div className="text-xs font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-950 px-3 py-1.5 rounded-lg">
                                {dl.showingStudents.replace("{n}", filteredStudents.length.toString()).replace("{m}", studentMetrics.length.toString())}
                            </div>
                        </div>

                        {filteredStudents.length === 0 ? (
                            <div className="flex flex-col items-center justify-center p-12 text-slate-400 dark:text-slate-500 text-sm">
                                <AlertCircle className="w-8 h-8 mb-2 text-slate-350" />
                                {dl.noStudentsMatched}
                            </div>
                        ) : (
                            <div className="overflow-x-auto w-full">
                                <table className="w-full border-collapse text-left text-sm">
                                    <thead>
                                        <tr className="border-b border-slate-200 dark:border-slate-700 bg-slate-50/75 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 font-semibold">
                                            <th 
                                                onClick={() => handleSort("name")}
                                                className="py-3.5 px-4 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-850 select-none"
                                            >
                                                <div className="flex items-center gap-1.5">
                                                    {dl.studentHeader} <ArrowUpDown className="w-3.5 h-3.5" />
                                                </div>
                                            </th>
                                            <th className="py-3.5 px-4">{dl.classHeader}</th>
                                            <th 
                                                onClick={() => handleSort("exams")}
                                                className="py-3.5 px-4 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-850 select-none text-center"
                                            >
                                                <div className="flex items-center justify-center gap-1.5">
                                                    {dl.examsHeader} <ArrowUpDown className="w-3.5 h-3.5" />
                                                </div>
                                            </th>
                                            <th 
                                                onClick={() => handleSort("accuracy")}
                                                className="py-3.5 px-4 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-850 select-none text-center"
                                            >
                                                <div className="flex items-center justify-center gap-1.5">
                                                    {dl.accuracyHeader} <ArrowUpDown className="w-3.5 h-3.5" />
                                                </div>
                                            </th>
                                            <th className="py-3.5 px-4">{dl.levelHeader}</th>
                                            <th className="py-3.5 px-4 text-right">{dl.actionsHeader}</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 dark:divide-slate-750">
                                        {filteredStudents.map((student) => {
                                            const isSelected = selectedStudent?.uuid === student.uuid;
                                            return (
                                                <tr 
                                                    key={student.uuid}
                                                    className={`hover:bg-slate-50/60 dark:hover:bg-slate-750/50 transition duration-150 ${
                                                        isSelected ? "bg-blue-50/40 dark:bg-blue-950/15" : ""
                                                    }`}
                                                >
                                                    <td className="py-3.5 px-4 font-medium text-slate-950 dark:text-white max-w-[180px] truncate">
                                                        {student.name}
                                                    </td>
                                                    <td className="py-3.5 px-4 text-slate-600 dark:text-slate-400 text-xs">
                                                        <div className="font-medium">{student.className}</div>
                                                        <div className="text-slate-450">{student.grade}</div>
                                                    </td>
                                                    <td className="py-3.5 px-4 text-center font-semibold text-slate-700 dark:text-slate-300">
                                                        {student.examsTaken.size}
                                                    </td>
                                                    <td className="py-3.5 px-4">
                                                        <div className="flex flex-col items-center gap-1">
                                                            <span className={`font-bold text-xs sm:text-sm ${
                                                                student.accuracy >= 80 
                                                                    ? "text-green-600 dark:text-green-450" 
                                                                    : student.accuracy >= 50 
                                                                        ? "text-blue-600 dark:text-blue-400" 
                                                                        : "text-amber-600 dark:text-amber-500"
                                                            }`}>
                                                                {student.accuracy.toFixed(0)}%
                                                            </span>
                                                            <div className="w-16 h-1.5 bg-slate-100 dark:bg-slate-900 rounded-full overflow-hidden">
                                                                <div
                                                                    className={`h-full rounded-full ${
                                                                        student.accuracy >= 80 
                                                                            ? "bg-green-500" 
                                                                            : student.accuracy >= 50 
                                                                                ? "bg-blue-500" 
                                                                                : "bg-amber-500"
                                                                    }`}
                                                                    style={{ width: `${student.accuracy}%` }}
                                                                />
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="py-3.5 px-4">
                                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                                                            student.latestRating.includes("4") || student.latestRating.toLowerCase().includes("leitor")
                                                                ? "bg-green-55 dark:bg-green-950/35 text-green-700 dark:text-green-400"
                                                                : student.latestRating.includes("3")
                                                                    ? "bg-blue-55 dark:bg-blue-950/35 text-blue-700 dark:text-blue-400"
                                                                    : "bg-amber-55 dark:bg-amber-950/35 text-amber-700 dark:text-amber-400"
                                                        }`}>
                                                            <Award className="w-3 h-3" />
                                                            {student.latestRating}
                                                        </span>
                                                    </td>
                                                    <td className="py-3.5 px-4 text-right">
                                                        <button
                                                            onClick={() => setSelectedStudent(isSelected ? null : student)}
                                                            className={`inline-flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-lg transition duration-150 ${
                                                                isSelected
                                                                    ? "bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300"
                                                                    : "bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/40 dark:hover:bg-blue-950/65 text-blue-600 dark:text-blue-450"
                                                            }`}
                                                        >
                                                            {isSelected ? dl.hideDetails : dl.viewDetails}
                                                            <ChevronRight className={`w-3 h-3 transform transition-transform duration-150 ${isSelected ? "rotate-90" : ""}`} />
                                                        </button>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Panel: Intervention Alert Board & Exam performance list */}
                <div className="flex flex-col gap-8">
                    {/* Intervention Board */}
                    <div className="bg-white dark:bg-slate-800 border border-red-100 dark:border-red-950/40 rounded-xl p-6 shadow-sm relative overflow-hidden">
                        <div className="absolute top-0 left-0 h-full w-1.5 bg-red-550 dark:bg-red-600" />
            
                        <div className="flex items-center gap-2.5 mb-4">
                            <div className="p-2 bg-red-50 dark:bg-red-950/40 rounded-lg text-red-600 dark:text-red-400">
                                <AlertCircle className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                                    {dl.interventionNeeded}
                                </h3>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                                    {dl.interventionSub}
                                </p>
                            </div>
                        </div>

                        {interventionStudents.length === 0 ? (
                            <div className="flex items-center justify-center py-6 bg-green-50 dark:bg-green-950/15 border border-green-100 dark:border-green-900 rounded-lg text-xs text-green-700 dark:text-green-400 font-medium gap-2">
                                <CheckCircle className="w-4 h-4" />
                                {dl.allStudentsFluency}
                            </div>
                        ) : (
                            <div className="flex flex-col gap-3 max-h-64 overflow-y-auto pr-1">
                                {interventionStudents.map((student) => (
                                    <div
                                        key={student.uuid}
                                        onClick={() => setSelectedStudent(student)}
                                        className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 dark:border-slate-750 hover:bg-slate-50 dark:hover:bg-slate-750 cursor-pointer transition duration-150"
                                    >
                                        <div className="flex flex-col min-w-0">
                                            <span className="text-sm font-semibold truncate text-slate-800 dark:text-slate-200">
                                                {student.name}
                                            </span>
                                            <span className="text-xs text-slate-500 dark:text-slate-455">
                                                {student.className} ({student.latestRating})
                                            </span>
                                        </div>
                                        <span className="px-2 py-1 bg-red-50 dark:bg-red-950/40 border border-red-100 dark:border-red-900 rounded-lg text-xs font-bold text-red-600 dark:text-red-400">
                                            {student.accuracy.toFixed(0)}% Acc
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* List: Exams Comparison */}
                    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
                        <div className="flex items-center gap-2.5 mb-6">
                            <div className="p-2 bg-blue-50 dark:bg-blue-950/40 rounded-lg text-blue-600 dark:text-blue-400">
                                <BookMarked className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                                    {dl.examsAssessment}
                                </h3>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                                    {dl.examsAssessmentSub}
                                </p>
                            </div>
                        </div>

                        {examOptions.length === 0 ? (
                            <div className="text-center py-6 text-slate-400 dark:text-slate-500 text-xs">
                                {dl.noExamsData}
                            </div>
                        ) : (
                            <div className="flex flex-col gap-4">
                                {examOptions.map((examName) => {
                                    // Calculate accuracy for this exam
                                    const examData = data.filter((row) => row.exam_name === examName);
                                    const totalHits = examData.reduce((sum, row) => sum + row.response_amount_hits, 0);
                                    const totalWords = examData.reduce((sum, row) => sum + row.question_amount_words, 0);
                                    const examAccuracy = totalWords > 0 ? (totalHits / totalWords) * 100 : 0;
                                    
                                    return (
                                        <div key={examName} className="flex flex-col border-b border-slate-100 dark:border-slate-750 pb-3 last:border-0 last:pb-0">
                                            <span className="text-sm font-bold text-slate-800 dark:text-slate-200 truncate" title={examName}>
                                                {examName}
                                            </span>
                                            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
                                                <span>{examData.length} {dl.totalResponses}</span>
                                                <span className={`font-bold ${
                                                    examAccuracy >= 70 
                                                        ? "text-green-600 dark:text-green-400" 
                                                        : "text-amber-600 dark:text-amber-500"
                                                }`}>
                                                    {examAccuracy.toFixed(1)}% accuracy
                                                </span>
                                            </div>
                                            <div className="w-full h-2 bg-slate-100 dark:bg-slate-900 rounded-full mt-2 overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full ${
                                                        examAccuracy >= 70 
                                                            ? "bg-gradient-to-r from-green-400 to-emerald-500" 
                                                            : "bg-gradient-to-r from-amber-400 to-orange-500"
                                                    }`}
                                                    style={{ width: `${examAccuracy}%` }}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Expandable Student Detail View Panel */}
            {selectedStudent && (
                <div className="bg-white dark:bg-slate-800 border border-blue-250 dark:border-blue-800 rounded-xl p-6 shadow-md mb-8 ring-2 ring-blue-400/30 dark:ring-blue-500/20 animate-fadeIn">
                    <div className="flex items-start justify-between flex-wrap gap-4 border-b border-slate-200 dark:border-slate-700 pb-5 mb-5">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center font-bold text-lg shadow-sm uppercase">
                                {selectedStudent.name.substring(0, 2)}
                            </div>
                            <div>
                                <h3 className="text-xl font-extrabold text-slate-950 dark:text-white">
                                    {selectedStudent.name}
                                </h3>
                                <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium">
                                    <span>{dl.classHeader.split("/")[0]}: <strong className="text-slate-700 dark:text-slate-350">{selectedStudent.className}</strong></span>
                                    <span>•</span>
                                    <span>{dl.classHeader.split("/")[1] || "Grade"}: <strong className="text-slate-700 dark:text-slate-350">{selectedStudent.grade}</strong></span>
                                    <span>•</span>
                                    <span>{dl.examsHeader} Taken: <strong className="text-slate-700 dark:text-slate-350">{selectedStudent.examsTaken.size}</strong></span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="text-center bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2">
                                <span className="text-xs text-slate-400 block uppercase tracking-wider font-semibold">{dl.avgAccuracy}</span>
                                <span className={`text-xl font-extrabold ${
                                    selectedStudent.accuracy >= 80 
                                        ? "text-green-600 dark:text-green-450" 
                                        : selectedStudent.accuracy >= 50 
                                            ? "text-blue-600 dark:text-blue-400" 
                                            : "text-amber-600 dark:text-amber-500"
                                }`}>
                                    {selectedStudent.accuracy.toFixed(1)}%
                                </span>
                            </div>
                            <button
                                onClick={() => setSelectedStudent(null)}
                                className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition duration-150"
                            >
                                <XCircle className="w-6 h-6" />
                            </button>
                        </div>
                    </div>

                    <h4 className="text-sm font-bold text-slate-800 dark:text-slate-250 mb-4 flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-blue-500" />
                        {dl.attemptsTimeline} ({selectedStudent.attempts.length} {dl.totalAttempts})
                    </h4>

                    <div className="flex flex-col gap-5 max-h-96 overflow-y-auto pr-2">
                        {selectedStudent.attempts.map((attempt, index) => {
                            const formattedDate = getFormattedDate(locale as string, new Date(attempt.timestamp));
                            return (
                                <div
                                    key={index}
                                    className="bg-slate-50 dark:bg-slate-900/55 border border-slate-200 dark:border-slate-750 rounded-xl p-4 flex flex-col gap-3"
                                >
                                    <div className="flex justify-between items-center flex-wrap gap-2">
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm font-bold text-slate-900 dark:text-slate-200">
                                                {attempt.examName}
                                            </span>
                                            <span className="text-[10px] font-semibold text-slate-400 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-1.5 py-0.5">
                                                {formattedDate}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 text-xs">
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                                attempt.accuracy >= 80 
                                                    ? "bg-green-100 dark:bg-green-950/40 text-green-700 dark:text-green-400" 
                                                    : attempt.accuracy >= 50 
                                                        ? "bg-blue-100 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400" 
                                                        : "bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-450"
                                            }`}>
                                                {dl.accuracyLabel} {attempt.accuracy.toFixed(0)}%
                                            </span>
                                            <span className="px-2 py-0.5 bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-full text-[10px] font-bold">
                                                {dl.fluencyLabel} {attempt.rating}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Highlighted word lists correct vs missed */}
                                    <div className="bg-white dark:bg-slate-900 border border-slate-150 dark:border-slate-700 rounded-lg p-3">
                                        <div className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 flex items-center gap-1.5">
                                            <span>{dl.readingResults}</span>
                                            <span className="text-slate-400">•</span>
                                            <span className="text-green-600 font-bold flex items-center gap-0.5">
                                                <CheckCircle className="w-3 h-3" /> {dl.correctWords} ({attempt.hits})
                                            </span>
                                            <span className="text-slate-400">•</span>
                                            <span className="text-red-500 font-bold flex items-center gap-0.5">
                                                <XCircle className="w-3 h-3" /> {dl.missedWords} ({attempt.totalWords - attempt.hits})
                                            </span>
                                        </div>
                                        <div className="flex flex-wrap gap-1.5 leading-relaxed text-sm">
                                            {attempt.wordsList.map((word, wIdx) => {
                                                // Check if the word matches response words (ignoring case and punctuation)
                                                const cleanWord = word.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?]/g,"");
                                                const isHit = attempt.responseWords.some(
                                                    (rw) => rw.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?]/g,"") === cleanWord
                                                );

                                                return (
                                                    <span
                                                        key={wIdx}
                                                        className={`px-1.5 py-0.5 rounded transition-all duration-150 ${
                                                            isHit
                                                                ? "bg-green-50 text-green-700 border border-green-200/60 dark:bg-green-950/25 dark:text-green-400 dark:border-green-900/40 font-medium"
                                                                : "bg-red-50 text-red-600 border border-red-100 dark:bg-red-950/25 dark:text-red-400 dark:border-red-950/40 hover:bg-red-100/70"
                                                        }`}
                                                        title={isHit ? "Word was read correctly" : "Word was missed or mispronounced"}
                                                    >
                                                        {word}
                                                    </span>
                                                );
                                            })}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
