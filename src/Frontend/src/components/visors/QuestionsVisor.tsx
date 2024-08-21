import React from 'react'
import { isEmpty } from 'lodash'
import { IQuestionEditor } from '@/interfaces/question';
import { QUESTION_TYPE_COMPLEX_WORDS, QUESTION_TYPE_MULTIPLE_CHOICE, QUESTION_TYPE_WORDS } from '@/constants/exams';
import { ENUM_QUESTION_STATUS_NOT_STARTED } from '@/constants/enums';

import TextVisor from '../text-visor/TextVisor';
import AnswersVisor from '../answers/AnswersVisor';
import AnswersResult from '../answers/AnswersResult';

type TQuestionVisorProps = {
    question: IQuestionEditor;
    results?: Array<string> | null;
    userResult?: boolean | null;
};

type TPhrasesAnswerVisorProps = {
    question: IQuestionEditor;
    results: Array<string>;
};

const PhrasesAnswerVisor : React.FC<TPhrasesAnswerVisorProps> = ({ question, results }) => {
    const regex = /[^a-zA-Z0-9\sáàâãäéèêëíìîïóòôõöúùûüçñÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ]/g;
    const removeSpecialCharFromQuestion = question.data.replace(regex, '').toUpperCase()
    const removeSpacesFromQuestion = removeSpecialCharFromQuestion.replace(/\s+/g, ' ').trim();
    const questionArr = removeSpacesFromQuestion.split(' ')
    const answerArr = results.join(' ').toUpperCase().split(' ')

    const compareTexts = (q: string[], a: string[]) => {
        const dp = Array(q.length + 1)
            .fill(null)
            .map(() => Array(a.length + 1).fill(0));

        for (let i = 0; i <= q.length; i++) {
            dp[i][0] = i;
        }
        
        for (let j = 0; j <= a.length; j++) {
            dp[0][j] = j;
        }

        for (let i = 1; i <= q.length; i++) {
            for (let j = 1; j <= a.length; j++) {
                if (q[i - 1].toUpperCase() === a[j - 1].toUpperCase()) {
                    dp[i][j] = dp[i - 1][j - 1];
                } else {
                    dp[i][j] = Math.min(dp[i - 1][j - 1], dp[i][j - 1], dp[i - 1][j]) + 1;
                }
            }
        }

        const result = [];
        let i = q.length;
        let j = a.length;

        while (i > 0 || j > 0) {
            if (i > 0 && j > 0 && q[i - 1].toUpperCase() === a[j - 1].toUpperCase()) {
                result.push({ word: a[j - 1], shouldHighlight: false });
                i--;
                j--;
            } else if (j > 0 && (i === 0 || dp[i][j - 1] <= dp[i - 1][j])) {
                result.push({ word: a[j - 1], shouldHighlight: true });
                j--;
            } else if (i > 0 && (j === 0 || dp[i - 1][j] <= dp[i][j - 1])) {
                i--;
            } else {
                result.push({ word: a[j - 1], shouldHighlight: true });
                i--;
                j--;
            }
        }

        return result.reverse();
    }

    const result = compareTexts(questionArr, answerArr);
    return <div className='flex flex-wrap gap-x-2'>{result.map((word, i)=> <span key={i} className={`${word.shouldHighlight && 'bg-red-500'}`}>{word.word}</span>)}</div>
}

const WordsVisor : React.FC<TQuestionVisorProps> = ({ question, results }) => {
    const words = question.data.split(" ");

    const shouldHighlight = (word: string) => {
        if (!words || isEmpty(words) || !results) return '';
        const answerWordsArray = results.join(' ').toUpperCase().split(' ');
   
        if (answerWordsArray.includes(word.toUpperCase())) {
            return 'bg-green-500 font-semibold text-white text-xs md:text-sm lg:text-base';
        }

        return 'bg-destructive font-semibold text-white text-xs md:text-sm lg:text-base';
    }


    return  ( 
        <div className="flex flex-col gap-4">
            <div className={`grid lg:grid-cols-3 grid-cols-1 md:grid-cols-2 w-full gap-2 overflow-y-auto pr-4` }
            >
                {Array.isArray(words) && words.map((word: string, i: number) => (
                    <div key={i} className={`${shouldHighlight(word)} p-2 rounded-md border overflow-hidden text-center w-full whitespace-nowrap text-ellipsis border-border dark:border-darkBorder dark:text-white`}>{word}</div>
                ))}
            </div>
        </div>
    );
}

const QuestionsVisor: React.FC<TQuestionVisorProps> = ({ question, results = null, userResult = null }) => {
    if (!question) return null;
    
    const type = question.type;
    
    if (type === QUESTION_TYPE_WORDS || type === QUESTION_TYPE_COMPLEX_WORDS) {
        return <WordsVisor question={question} results={results} userResult={userResult} />
    }

    const userAnswer = results?.join(' ') || ' '

    if (type === QUESTION_TYPE_MULTIPLE_CHOICE) {
        return (
            <div className='flex flex-col gap-4'>
                {!results && (
                    <TextVisor data={results ? userAnswer : question.formatted_data} />
                )}
                {question.status !== ENUM_QUESTION_STATUS_NOT_STARTED && (
                    <>
                        {results ? <AnswersResult question={question} results={results} /> : <AnswersVisor question={question} />}
                    </>
                )}
            </div>
        )
    }

    
    if (results) {
        return  <PhrasesAnswerVisor question={question} results={results} />
    }

    return (
        <TextVisor data={question.formatted_data} />
    );
}

export default QuestionsVisor;