'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import axios from 'axios';
import { api } from '@/api/api';
import { 
    ICON_BOOK_OPEN, 
    ICON_CLOUD_ARROW_UP, 
    ICON_X_MARK,
    ICON_DOCUMENT_TEXT,
    ICON_PRESENTATION_CHART_BAR,
    ICON_MAGNIFYING_GLASS,
    ICON_ARROWS_POINTING_OUT,
    ICON_ARROWS_POINTING_IN,
    ICON_PLAY,
    ICON_ARROW_PATH
} from '@/constants/icons';
import useIcon from '@/hooks/useIcon';
import * as Progress from '@radix-ui/react-progress';
import { toast } from 'react-toastify';
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface KBFile {
    id: string;
    filename: string;
    content_type: string;
    size_bytes: number;
    status: string;
    indexing_status: string;
    vector_status: string;
    description?: string;
    created_at: string;
}

interface UploadingFile {
    id: string;
    file: File;
    progress: number;
    status: 'pending' | 'uploading' | 'confirming' | 'completed' | 'failed';
    error?: string;
}

const KnowledgeBase: React.FC = () => {
    const t = useTranslations('knowledge_base');
    const tTable = useTranslations('table.pagination');
    const tCommon = useTranslations('common');
    const { getIcon } = useIcon();

    const [fileToDelete, setFileToDelete] = useState<{ id: string; name: string } | null>(null);

    const [fileToView, setFileToView] = useState<KBFile | null>(null);
    const [viewUrl, setViewUrl] = useState<string | null>(null);
    const [isViewLoading, setIsViewLoading] = useState(false);
    const [viewSize, setViewSize] = useState<'large' | 'fullscreen'>('large');

    const handleViewFile = async (fileItem: KBFile) => {
        setFileToView(fileItem);
        setIsViewLoading(true);
        try {
            const response = await api.get(`/admin/knowledge-base/files/${fileItem.id}/view`);
            setViewUrl(response.data.url);
        } catch (err: any) {
            console.error('Failed to get view URL:', err);
            toast.error(t('error_view') || 'Failed to retrieve file preview');
            setFileToView(null);
        } finally {
            setIsViewLoading(false);
        }
    };

    const handleRetryFile = async (fileId: string) => {
        try {
            // Optimistically update status to processing
            setFilesList(prev => prev.map(f => {
                if (f.id === fileId) {
                    return {
                        ...f,
                        status: 'processing',
                        indexing_status: 'pending',
                        vector_status: 'pending'
                    };
                }
                return f;
            }));
            
            await api.post(`/admin/knowledge-base/files/${fileId}/retry`);
            toast.success(t('success_retry') || 'Processing retried successfully');
            fetchFiles(currentPage);
        } catch (err: any) {
            console.error('Failed to retry file processing:', err);
            toast.error(t('error_retry') || 'Failed to retry file processing');
            fetchFiles(currentPage);
        }
    };

    const handleRetryUpload = (uf: UploadingFile) => {
        setUploadingFiles(prev => prev.map(p => p.id === uf.id ? { ...p, status: 'pending', progress: 0, error: undefined } : p));
        uploadFilesBatch([uf]);
    };

    const [isDragging, setIsDragging] = useState(false);
    const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
    const [filesList, setFilesList] = useState<KBFile[]>([]);
    const [totalCount, setTotalCount] = useState(0);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize] = useState(10);
    const [isLoading, setIsLoading] = useState(false);

    const getIndexingStatusClass = (status: string) => {
        if (status === 'completed') return 'bg-green-100 text-green-700 dark:bg-green-950/20 dark:text-green-400';
        if (status === 'failed') return 'bg-red-100 text-red-700 dark:bg-red-950/20 dark:text-red-400';
        return 'bg-amber-100 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400';
    };

    const getVectorStatusClass = (status: string) => {
        if (status === 'completed') return 'bg-green-100 text-green-700 dark:bg-green-950/20 dark:text-green-400';
        if (status === 'failed') return 'bg-red-100 text-red-700 dark:bg-red-950/20 dark:text-red-400';
        return 'bg-amber-100 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400';
    };

    const getFileStatusClass = (status: string) => {
        if (status === 'completed') return 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400';
        if (status === 'failed') return 'bg-rose-500/10 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400';
        if (status === 'processing') return 'bg-sky-500/10 text-sky-600 dark:bg-sky-500/20 dark:text-sky-400 animate-pulse';
        return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400';
    };

    // Fetch files list
    const fetchFiles = useCallback(async (page: number) => {
        setIsLoading(true);
        try {
            const res = await api.get('/admin/knowledge-base/files', {
                params: { page, size: pageSize }
            });
            setFilesList(res.data.items);
            setTotalCount(res.data.total);
        } catch (err) {
            console.error('Failed to load KB files', err);
            toast.error(t('error_load_list') || 'Failed to load files list');
        } finally {
            setIsLoading(false);
        }
    }, [pageSize, t]);

    useEffect(() => {
        fetchFiles(currentPage);
    }, [currentPage, fetchFiles]);

    // Polling active processing files every 8 seconds
    useEffect(() => {
        const activeFiles = filesList.some(f => ['registering', 'uploaded', 'processing'].includes(f.status));
        if (!activeFiles) return;

        const interval = setInterval(() => {
            fetchFiles(currentPage);
        }, 8000);

        return () => clearInterval(interval);
    }, [filesList, currentPage, fetchFiles]);

    // Drag-and-drop event handlers
    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const processSelectedFiles = (selectedFiles: FileList) => {
        const allowedTypes = [
            'application/pdf',
            'video/mp4',
            'video/webm',
            'audio/mpeg',
            'audio/mp3',
            'audio/wav',
            'audio/x-wav'
        ];

        const validFiles: UploadingFile[] = [];
        for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];
            if (!allowedTypes.includes(file.type)) {
                toast.warning(`${file.name}: ${t('invalid_type_warning') || 'File type not allowed'}`);
                continue;
            }

            let limit = 50 * 1024 * 1024; // Default fallback (50MB)
            let limitLabel = "50MB";

            if (file.type === 'application/pdf') {
                limit = 200 * 1024 * 1024; // 200MB
                limitLabel = "200MB";
            } else if (file.type.startsWith('video/')) {
                limit = 5 * 1024 * 1024 * 1024; // 5GB
                limitLabel = "5GB";
            } else if (file.type.startsWith('audio/')) {
                limit = 500 * 1024 * 1024; // 500MB
                limitLabel = "500MB";
            }

            if (file.size > limit) {
                toast.warning(`${file.name}: ${t('file_size_warning', { limit: limitLabel }) || `File exceeds ${limitLabel} limit`}`);
                continue;
            }

            validFiles.push({
                id: Math.random().toString(36).substring(7),
                file,
                progress: 0,
                status: 'pending'
            });
        }

        if (validFiles.length > 0) {
            setUploadingFiles(prev => [...prev, ...validFiles]);
            // Auto trigger upload
            uploadFilesBatch(validFiles);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files) {
            processSelectedFiles(e.dataTransfer.files);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            processSelectedFiles(e.target.files);
        }
    };

    // Parallel upload orchestration
    const uploadFilesBatch = async (batch: UploadingFile[]) => {
        const registerPayload = {
            files: batch.map(f => ({
                filename: f.file.name,
                content_type: f.file.type,
                size_bytes: f.file.size
            }))
        };

        try {
            // 1. Register Uploads to backend
            const regRes = await api.post('/admin/knowledge-base/register-uploads', registerPayload);
            const registeredItems = regRes.data.files;

            // Map frontend upload files to their DB IDs
            const updatedBatch = batch.map((f, index) => ({
                ...f,
                id: registeredItems[index].id,
                signedUrl: registeredItems[index].signed_url
            }));

            // Update uploading files status to 'uploading'
            setUploadingFiles(prev => 
                prev.map(p => {
                    const match = updatedBatch.find(u => u.file.name === p.file.name && p.status === 'pending');
                    return match ? { ...p, id: match.id, status: 'uploading' } : p;
                })
            );

            // 2. Perform PUT uploads in parallel
            await Promise.all(updatedBatch.map(async (uItem) => {
                try {
                    // Direct binary upload to GCS (must NOT use 'api' client instance to avoid auth headers mismatch)
                    if (uItem.signedUrl.includes('test-bucket') || uItem.signedUrl.includes('mock')) {
                        // Mock upload progress in local/dev mode
                        for (let p = 0; p <= 100; p += 25) {
                            setUploadingFiles(prev => 
                                prev.map(p2 => p2.id === uItem.id ? { ...p2, progress: p } : p2)
                            );
                            await new Promise(r => setTimeout(r, 80));
                        }
                    } else {
                        // Real upload to GCS
                        await axios.put(uItem.signedUrl, uItem.file, {
                            headers: { 'Content-Type': uItem.file.type },
                            onUploadProgress: (prog) => {
                                const pct = Math.round((prog.loaded * 100) / (prog.total || uItem.file.size));
                                setUploadingFiles(prev => 
                                    prev.map(p => p.id === uItem.id ? { ...p, progress: pct } : p)
                                );
                            }
                        });
                    }

                    // 3. Confirm upload
                    setUploadingFiles(prev => 
                        prev.map(p => p.id === uItem.id ? { ...p, status: 'confirming' } : p)
                    );
                    await api.post(`/admin/knowledge-base/files/${uItem.id}/confirm-upload`);

                    setUploadingFiles(prev => 
                        prev.map(p => p.id === uItem.id ? { ...p, status: 'completed', progress: 100 } : p)
                    );
                    toast.success(`${uItem.file.name}: ${t('upload_success') || 'Uploaded successfully'}`);
                    setTimeout(() => {
                        setUploadingFiles(prev => prev.filter(p => p.id !== uItem.id));
                    }, 1500);
                } catch (err: any) {
                    console.error('Upload failed for', uItem.file.name, err);
                    setUploadingFiles(prev => 
                        prev.map(p => p.id === uItem.id ? { ...p, status: 'failed', error: err.message } : p)
                    );
                    toast.error(`${uItem.file.name}: ${t('error_upload') || 'Failed to upload'}`);
                }
            }));

            // Refresh file monitor list
            fetchFiles(currentPage);
        } catch (err: any) {
            console.error('Batch registration failed', err);
            toast.error(t('error_register_batch') || 'Failed to register files batch');
            // Fail all files in batch
            setUploadingFiles(prev => 
                prev.map(p => batch.some(b => b.file.name === p.file.name && p.status === 'pending') ? { ...p, status: 'failed', error: err.message } : p)
            );
        }
    };

    // Delete handler
    const confirmDeleteFile = async (id: string) => {
        try {
            await api.delete(`/admin/knowledge-base/files/${id}`);
            toast.success(t('delete_success') || 'File deleted successfully');
            fetchFiles(currentPage);
        } catch (err) {
            console.error('Failed to delete file', err);
            toast.error(t('error_delete') || 'Failed to delete file');
        } finally {
            setFileToDelete(null);
        }
    };

    // Format bytes to human readable format
    const formatBytes = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <div className="flex flex-col gap-6 w-full h-full p-6 text-slate-800 dark:text-slate-100">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold tracking-tight text-primary dark:text-white flex items-center gap-2">
                    <span className="w-8 h-8 flex items-center justify-center">
                        {getIcon({ icon: ICON_BOOK_OPEN, classes: 'text-primary dark:text-sky-400' })}
                    </span>
                    {t('title')}
                </h1>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    {t('subtitle')}
                </p>
            </div>

            {/* Upload Zone */}
            <div 
                className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all cursor-pointer bg-white dark:bg-slate-900/40 relative ${
                    isDragging 
                        ? 'border-sky-500 bg-sky-50/20 dark:border-sky-400 dark:bg-sky-950/10 scale-[1.01]' 
                        : 'border-slate-300 hover:border-slate-400 dark:border-slate-700 dark:hover:border-slate-600'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById('kb-file-input')?.click()}
            >
                <input 
                    type="file" 
                    id="kb-file-input" 
                    className="hidden" 
                    multiple
                    accept=".pdf,.mp4,.webm,.mp3,.wav"
                    onChange={handleFileChange}
                />
                <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                    {getIcon({ icon: ICON_CLOUD_ARROW_UP, classes: 'w-6 h-6 text-slate-500 dark:text-slate-400' })}
                </div>
                <p className="text-base font-semibold text-slate-700 dark:text-slate-300">
                    {t('upload_zone')}
                </p>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                    {t('upload_hint')}
                </p>
            </div>

            {/* Active Uploads Progress */}
            {uploadingFiles.length > 0 && (
                <div className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-xl p-4 flex flex-col gap-3 shadow-sm">
                    <div className="flex justify-between items-center pb-2 border-b border-slate-100 dark:border-slate-800">
                        <h3 className="font-semibold text-sm">{t('uploading')}</h3>
                        <button 
                            onClick={() => setUploadingFiles([])}
                            className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 transition-colors"
                        >
                            {getIcon({ icon: ICON_X_MARK, classes: 'w-4 h-4' })}
                        </button>
                    </div>
                    <div className="flex flex-col gap-3 max-h-[200px] overflow-y-auto pr-2">
                        {uploadingFiles.map((uf) => (
                            <div key={uf.id} className="flex flex-col gap-1.5 text-xs">
                                <div className="flex justify-between font-medium">
                                    <span className="truncate max-w-[70%]">{uf.file.name}</span>
                                    <div className="flex items-center gap-1.5">
                                        <span className={uf.status === 'completed' ? 'text-green-500' : uf.status === 'failed' ? 'text-red-500' : 'text-slate-500'}>
                                            {uf.status === 'completed' ? t('completed') : uf.status === 'failed' ? uf.error || t('failed') : `${uf.progress}%`}
                                        </span>
                                        {uf.status === 'failed' && (
                                            <button
                                                onClick={() => handleRetryUpload(uf)}
                                                className="w-5 h-5 flex items-center justify-center rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 hover:text-slate-700 transition-colors"
                                                title={t('retry') || 'Retry'}
                                            >
                                                {getIcon({ icon: ICON_ARROW_PATH, classes: 'w-3 h-3' })}
                                            </button>
                                        )}
                                    </div>
                                </div>
                                <Progress.Root 
                                    className="relative overflow-hidden bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 w-full"
                                    value={uf.progress}
                                >
                                    <Progress.Indicator 
                                        className="bg-sky-500 dark:bg-sky-400 h-full transition-all duration-300"
                                        style={{ transform: `translateX(-${100 - uf.progress}%)` }}
                                    />
                                </Progress.Root>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Monitoring Table */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden flex flex-col flex-1">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-sm">
                        <thead>
                            <tr className="bg-slate-50 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-800 font-semibold text-slate-500 dark:text-slate-400">
                                <th className="p-4">{t('filename')}</th>
                                <th className="p-4">{t('content_type')}</th>
                                <th className="p-4">{t('size')}</th>
                                <th className="p-4 text-center">{t('indexing')}</th>
                                <th className="p-4 text-center">{t('vector')}</th>
                                <th className="p-4 text-center">{t('status')}</th>
                                <th className="p-4 text-right">{t('actions')}</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {isLoading && filesList.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="p-8 text-center text-slate-400">
                                        {t('loading')}
                                    </td>
                                </tr>
                            ) : filesList.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="p-8 text-center text-slate-400">
                                        {t('no_data') || 'No pedagogical files uploaded yet.'}
                                    </td>
                                </tr>
                            ) : (
                                filesList.map((file) => (
                                    <tr key={file.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20">
                                        <td className="p-4 font-medium truncate max-w-[200px]" title={file.filename}>
                                            {file.filename}
                                        </td>
                                        <td className="p-4 text-slate-500 dark:text-slate-400 text-xs">
                                            {file.content_type}
                                        </td>
                                        <td className="p-4 text-slate-500 dark:text-slate-400">
                                            {formatBytes(file.size_bytes)}
                                        </td>
                                        <td className="p-4 text-center">
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getIndexingStatusClass(file.indexing_status)}`}>
                                                {t(file.indexing_status)}
                                            </span>
                                        </td>
                                        <td className="p-4 text-center">
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getVectorStatusClass(file.vector_status)}`}>
                                                {t(file.vector_status)}
                                            </span>
                                        </td>
                                        <td className="p-4 text-center">
                                            <span className={`px-2 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${getFileStatusClass(file.status)}`}>
                                                {t(file.status)}
                                            </span>
                                        </td>
                                        <td className="p-4 text-right">
                                            <div className="flex items-center justify-end gap-1.5">
                                                {file.status === 'completed' && (
                                                    <button 
                                                        onClick={() => handleViewFile(file)}
                                                        className="w-8 h-8 flex items-center justify-center rounded-md text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                                        title={t('view') || "View File"}
                                                    >
                                                        {getIcon({ icon: ICON_MAGNIFYING_GLASS, classes: 'w-4 h-4' })}
                                                    </button>
                                                )}
                                                {file.status === 'failed' && (
                                                    <button 
                                                        onClick={() => handleRetryFile(file.id)}
                                                        className="w-8 h-8 flex items-center justify-center rounded-md text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                                        title={t('retry') || "Retry"}
                                                    >
                                                        {getIcon({ icon: ICON_ARROW_PATH, classes: 'w-4 h-4' })}
                                                    </button>
                                                )}
                                                <button 
                                                    onClick={() => setFileToDelete({ id: file.id, name: file.filename })}
                                                    className="w-8 h-8 flex items-center justify-center rounded-md text-slate-400 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                                    title={t('delete') || "Delete file"}
                                                >
                                                    {getIcon({ icon: ICON_X_MARK, classes: 'w-4 h-4' })}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination footer */}
                {totalCount > pageSize && (
                    <div className="flex justify-between items-center p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850/10 text-xs">
                        <span className="text-slate-500 dark:text-slate-400">
                            {tTable('showing')} {Math.min((currentPage - 1) * pageSize + 1, totalCount)} {tTable('to')} {Math.min(currentPage * pageSize, totalCount)} {tTable('of')} {totalCount} {t('files')}
                        </span>
                        <div className="flex gap-2">
                            <button
                                disabled={currentPage === 1}
                                onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
                                className="px-3 py-1 border border-slate-200 dark:border-slate-800 rounded hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 disabled:hover:bg-transparent"
                            >
                                {tTable('previous')}
                            </button>
                            <button
                                disabled={currentPage * pageSize >= totalCount}
                                onClick={() => setCurrentPage(p => p + 1)}
                                className="px-3 py-1 border border-slate-200 dark:border-slate-800 rounded hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 disabled:hover:bg-transparent"
                            >
                                {tTable('next')}
                            </button>
                        </div>
                    </div>
                )}

                {/* Delete Confirmation Modal */}
                <Dialog open={!!fileToDelete} onOpenChange={(open) => !open && setFileToDelete(null)}>
                    <DialogContent className="max-w-[400px] sm:max-w-[500px]">
                        <DialogHeader>
                            <DialogTitle className="text-red-500 flex items-center gap-2">
                                {t('delete_title')}
                            </DialogTitle>
                        </DialogHeader>
                        <div className="py-4 text-sm text-slate-500 dark:text-slate-400">
                            <p>{t('delete_confirm')}</p>
                            <p className="font-semibold text-slate-800 dark:text-slate-200 mt-2 p-2 bg-slate-50 dark:bg-slate-850/40 rounded border border-slate-100 dark:border-slate-800 truncate">
                                {fileToDelete?.name}
                            </p>
                        </div>
                        <DialogFooter className="gap-2 sm:gap-0">
                            <Button variant="ghost" onClick={() => setFileToDelete(null)}>
                                {tCommon('cancel')}
                            </Button>
                            <Button variant="destructive" onClick={() => fileToDelete && confirmDeleteFile(fileToDelete.id)}>
                                {tCommon('confirm')}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                {/* File Viewer Modal */}
                <Dialog open={fileToView !== null} onOpenChange={(open) => {
                    if (!open) {
                        setFileToView(null);
                        setViewUrl(null);
                    }
                }}>
                    <DialogContent className={`flex flex-col p-0 gap-0 overflow-hidden transition-all duration-200 border border-slate-200 dark:border-slate-800 ${
                        viewSize === 'fullscreen' 
                            ? 'max-w-none w-screen h-screen rounded-none' 
                            : 'max-w-5xl w-[90vw] h-[85vh]'
                    }`}>
                        {/* Header */}
                        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-100 dark:border-slate-800 shrink-0">
                            <div className="flex flex-col min-w-0 pr-4">
                                <DialogTitle className="font-semibold text-base text-slate-800 dark:text-slate-200 truncate">
                                    {fileToView?.filename}
                                </DialogTitle>
                                <span className="text-xs text-slate-400 dark:text-slate-500">
                                    {fileToView?.content_type} • {(fileToView ? fileToView.size_bytes / (1024 * 1024) : 0).toFixed(2)} MB
                                </span>
                            </div>
                            <div className="flex items-center gap-2 pr-6">
                                {/* Size Toggle Button */}
                                <button
                                    onClick={() => setViewSize(prev => prev === 'large' ? 'fullscreen' : 'large')}
                                    className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
                                    title={viewSize === 'large' ? t('fullscreen') || 'Fullscreen' : t('exit_fullscreen') || 'Exit Fullscreen'}
                                >
                                    {getIcon({ 
                                        icon: viewSize === 'large' ? ICON_ARROWS_POINTING_OUT : ICON_ARROWS_POINTING_IN, 
                                        classes: 'w-4 h-4' 
                                    })}
                                </button>
                            </div>
                        </div>

                        {/* Content Area */}
                        <div className="flex-1 min-h-0 flex flex-col md:flex-row divide-y md:divide-y-0 md:divide-x divide-slate-100 dark:divide-slate-800">
                            {/* Player / Viewer */}
                            <div className="flex-1 min-w-0 bg-slate-50 dark:bg-slate-950 flex items-center justify-center relative p-4">
                                {isViewLoading ? (
                                    <div className="flex flex-col items-center gap-2 text-slate-400">
                                        <div className="animate-spin w-8 h-8 border-4 border-sky-500 border-t-transparent rounded-full" />
                                        <span className="text-xs">{t('loading')}</span>
                                    </div>
                                ) : viewUrl ? (
                                    <>
                                        {fileToView?.content_type === 'application/pdf' && (
                                            <iframe 
                                                src={`${viewUrl}#toolbar=0`} 
                                                className="w-full h-full rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800" 
                                            />
                                        )}
                                        {fileToView?.content_type.startsWith('video/') && (
                                            <video 
                                                src={viewUrl} 
                                                controls 
                                                className="w-full max-h-full rounded-lg shadow-sm bg-black" 
                                            />
                                        )}
                                        {fileToView?.content_type.startsWith('audio/') && (
                                            <div className="w-full max-w-md bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-md border border-slate-100 dark:border-slate-800 flex flex-col gap-4">
                                                <div className="flex items-center justify-center w-16 h-16 rounded-full bg-sky-50 dark:bg-sky-950/40 text-sky-500 dark:text-sky-400 mx-auto">
                                                    {getIcon({ icon: ICON_PLAY, classes: 'w-8 h-8 ml-1' })}
                                                </div>
                                                <audio src={viewUrl} controls className="w-full" />
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <span className="text-xs text-slate-400">{t('error_load_content') || "Failed to load content"}</span>
                                )}
                            </div>

                            {/* Description Panel */}
                            <div className="w-full md:w-80 shrink-0 p-6 flex flex-col gap-4 overflow-y-auto bg-white dark:bg-slate-900">
                                <h4 className="font-semibold text-sm text-slate-700 dark:text-slate-300">
                                    {t('ai_description') || 'AI Description'}
                                </h4>
                                <div className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed bg-slate-50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-100 dark:border-slate-800 whitespace-pre-wrap">
                                    {fileToView?.description || t('no_description_available') || 'No description available for this file.'}
                                </div>
                            </div>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>
        </div>
    );
};

export default KnowledgeBase;
