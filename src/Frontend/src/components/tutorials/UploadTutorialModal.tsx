'use client'

import React, { useState, useRef } from 'react';
import { useTranslations } from 'next-intl';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import useIcon from '@/hooks/useIcon';
import { ICON_CLOUD_ARROW_UP, ICON_CLIPBOARD_CHECK, ICON_COG, ICON_ACADEMIC_CAP } from '@/constants/icons';
import { api } from '@/api/api';
import Alert from '@/classes/Alert';
import { ALERT_SUCCESS, ALERT_ERROR } from '@/constants/alerts';

interface UploadTutorialModalProps {
    isOpen: boolean;
    onClose: () => void;
    locale: string;
    onSuccess: () => void;
}

const UploadTutorialModal: React.FC<UploadTutorialModalProps> = ({ isOpen, onClose, locale, onSuccess }) => {
    const tCommon = useTranslations("common");
    
    const { getIcon } = useIcon();
    
    const [audience, setAudience] = useState<'educator' | 'admin'>('educator');
    const [sourceType, setSourceType] = useState<'upload' | 'link'>('upload');
    const [url, setUrl] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const droppedFile = e.dataTransfer.files[0];
            if (droppedFile.type === "application/pdf") {
                setFile(droppedFile);
            } else {
                new Alert().alert(ALERT_ERROR, "toast.errors.form.file_csv"); // Fallback or custom PDF error format
            }
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);

        try {
            const formData = new FormData();
            formData.append('audience', audience);
            formData.append('source_type', sourceType);
            
            if (sourceType === 'upload') {
                if (!file) {
                    new Alert().alert(ALERT_ERROR, "toast.errors.form.file_required");
                    setIsSubmitting(false);
                    return;
                }
                formData.append('file', file);
            } else {
                if (!url.trim()) {
                    new Alert().alert(ALERT_ERROR, "toast.errors.form.cant_be_empty");
                    setIsSubmitting(false);
                    return;
                }
                formData.append('url', url);
            }

            await api.post('/tutorials', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                }
            });

            new Alert().alert(ALERT_SUCCESS, "toast.success.form.tutorial_created");
            onSuccess();
            onClose();
            // Reset form
            setFile(null);
            setUrl('');
        } catch (error) {
            console.error("Upload tutorial failed", error);
            new Alert().alert(ALERT_ERROR, "toast.errors.form.create_tutorial");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[500px] p-6 bg-white dark:bg-darkBackground border dark:border-darkBorder text-neutral-900 dark:text-white">
                <DialogHeader>
                    <DialogTitle className="text-xl font-bold text-center md:text-left">
                        {locale === 'pt-BR' ? 'Upload de Tutorial' : locale === 'es-ES' ? 'Subir Tutorial' : 'Upload Tutorial'}
                    </DialogTitle>
                    <DialogDescription className="text-sm text-neutral-500 dark:text-neutral-400 text-center md:text-left">
                        {locale === 'pt-BR' ? 'Selecione o público-alvo, tipo de fonte e preencha os dados.' : 'Select the target audience, source type, and fill in the details.'}
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="flex flex-col gap-6 mt-2">
                    {/* Target Audience Segment */}
                    <div className="flex flex-col gap-2">
                        <Label className="text-sm font-medium">
                            {locale === 'pt-BR' ? 'Público-Alvo' : 'Target Audience'}
                        </Label>
                        <RadioGroup 
                            value={audience} 
                            onValueChange={(v: any) => setAudience(v)}
                            className="grid grid-cols-2 gap-4"
                        >
                            <div>
                                <RadioGroupItem value="educator" id="audience-educator" className="peer sr-only" />
                                <Label
                                    htmlFor="audience-educator"
                                    className={`flex items-center justify-center gap-2 p-3 rounded-lg border cursor-pointer transition-all duration-150 ${
                                        audience === 'educator' 
                                            ? 'border-primary dark:border-darkPrimary bg-primary/5 text-primary dark:text-darkPrimary' 
                                            : 'border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900'
                                    }`}
                                >
                                    <div className="w-5 h-5">{getIcon({ icon: ICON_ACADEMIC_CAP })}</div>
                                    <span>{locale === 'pt-BR' ? 'Educadores' : 'Educators'}</span>
                                </Label>
                            </div>

                            <div>
                                <RadioGroupItem value="admin" id="audience-admin" className="peer sr-only" />
                                <Label
                                    htmlFor="audience-admin"
                                    className={`flex items-center justify-center gap-2 p-3 rounded-lg border cursor-pointer transition-all duration-150 ${
                                        audience === 'admin' 
                                            ? 'border-primary dark:border-darkPrimary bg-primary/5 text-primary dark:text-darkPrimary' 
                                            : 'border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900'
                                    }`}
                                >
                                    <div className="w-5 h-5">{getIcon({ icon: ICON_COG })}</div>
                                    <span>{locale === 'pt-BR' ? 'Administradores' : 'Administrators'}</span>
                                </Label>
                            </div>
                        </RadioGroup>
                    </div>

                    {/* Source Type Segment */}
                    <div className="flex flex-col gap-2">
                        <Label className="text-sm font-medium">
                            {locale === 'pt-BR' ? 'Tipo de Recurso' : 'Source Type'}
                        </Label>
                        <RadioGroup 
                            value={sourceType} 
                            onValueChange={(v: any) => setSourceType(v)}
                            className="grid grid-cols-2 gap-4"
                        >
                            <div>
                                <RadioGroupItem value="upload" id="source-upload" className="peer sr-only" />
                                <Label
                                    htmlFor="source-upload"
                                    className={`flex items-center justify-center p-2 rounded-lg border cursor-pointer text-center transition-all duration-150 text-sm ${
                                        sourceType === 'upload' 
                                            ? 'border-primary dark:border-darkPrimary bg-primary/5 text-primary dark:text-darkPrimary' 
                                            : 'border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900'
                                    }`}
                                >
                                    {locale === 'pt-BR' ? 'Fazer Upload' : 'Upload File'}
                                </Label>
                            </div>

                            <div>
                                <RadioGroupItem value="link" id="source-link" className="peer sr-only" />
                                <Label
                                    htmlFor="source-link"
                                    className={`flex items-center justify-center p-2 rounded-lg border cursor-pointer text-center transition-all duration-150 text-sm ${
                                        sourceType === 'link' 
                                            ? 'border-primary dark:border-darkPrimary bg-primary/5 text-primary dark:text-darkPrimary' 
                                            : 'border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900'
                                    }`}
                                >
                                    {locale === 'pt-BR' ? 'Link Público' : 'Public Link'}
                                </Label>
                            </div>
                        </RadioGroup>
                    </div>

                    {/* Dynamic Input Fields */}
                    {sourceType === 'upload' ? (
                        <div className="flex flex-col gap-2">
                            <Label className="text-sm font-medium">
                                {locale === 'pt-BR' ? 'Arquivo PDF' : 'PDF File'}
                            </Label>
                            
                            <div 
                                onDragEnter={handleDrag} 
                                onDragOver={handleDrag} 
                                onDragLeave={handleDrag} 
                                onDrop={handleDrop}
                                onClick={() => fileInputRef.current?.click()}
                                className={`flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-150 ${
                                    dragActive 
                                        ? 'border-primary dark:border-darkPrimary bg-primary/5 scale-[0.99]' 
                                        : 'border-neutral-300 dark:border-neutral-800 hover:border-neutral-400 dark:hover:border-neutral-700 hover:bg-neutral-50/50 dark:hover:bg-neutral-900/30'
                                }`}
                            >
                                <input 
                                    ref={fileInputRef}
                                    type="file" 
                                    accept="application/pdf" 
                                    onChange={handleFileChange}
                                    className="hidden" 
                                />
                                
                                {file ? (
                                    <div className="flex flex-col items-center gap-2 text-center">
                                        <div className="w-10 h-10 text-green-500 dark:text-green-400">
                                            {getIcon({ icon: ICON_CLIPBOARD_CHECK, classes: "w-10 h-10" })}
                                        </div>
                                        <span className="text-sm font-semibold truncate max-w-[300px]">{file.name}</span>
                                        <span className="text-xs text-neutral-500 dark:text-neutral-400">
                                            {(file.size / (1024 * 1024)).toFixed(2)} MB
                                        </span>
                                        <button 
                                            type="button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setFile(null);
                                            }}
                                            className="mt-2 text-xs text-red-500 hover:underline"
                                        >
                                            {locale === 'pt-BR' ? 'Remover' : 'Remove'}
                                        </button>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center gap-2 text-center">
                                        <div className="w-12 h-12 text-neutral-400 dark:text-neutral-600">
                                            {getIcon({ icon: ICON_CLOUD_ARROW_UP, classes: "w-12 h-12" })}
                                        </div>
                                        <span className="text-sm font-medium">
                                            {locale === 'pt-BR' ? 'Arraste e solte seu PDF aqui ou clique para buscar' : 'Drag and drop your PDF here, or click to browse'}
                                        </span>
                                        <span className="text-xs text-neutral-400 dark:text-neutral-500">
                                            {locale === 'pt-BR' ? 'Apenas arquivos PDF até 10MB' : 'Only PDF files up to 10MB'}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col gap-2">
                            <Label htmlFor="public-url" className="text-sm font-medium">
                                {locale === 'pt-BR' ? 'URL Pública do Arquivo' : 'Public File URL'}
                            </Label>
                            <Input 
                                id="public-url"
                                type="url" 
                                placeholder="https://example.com/tutorial.pdf"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                className="w-full p-3 border dark:border-neutral-800 rounded-lg dark:bg-neutral-950 text-neutral-900 dark:text-white"
                            />
                        </div>
                    )}

                    {/* Dialog Actions */}
                    <DialogFooter className="flex gap-3 justify-end mt-4">
                        <Button 
                            type="button" 
                            onClick={onClose} 
                            variant="ghost"
                            disabled={isSubmitting}
                            className="px-5 py-2 rounded-lg dark:text-white dark:hover:bg-neutral-800"
                        >
                            {tCommon("cancel")}
                        </Button>
                        <Button 
                            type="submit"
                            disabled={isSubmitting}
                            className="px-5 py-2 rounded-lg text-white bg-primary dark:bg-darkPrimary hover:opacity-90 font-semibold"
                        >
                            {isSubmitting ? (
                                <div className="flex items-center gap-2">
                                    <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                                    <span>{locale === 'pt-BR' ? 'Enviando...' : 'Uploading...'}</span>
                                </div>
                            ) : (
                                <span>{tCommon("save")}</span>
                            )}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default UploadTutorialModal;
