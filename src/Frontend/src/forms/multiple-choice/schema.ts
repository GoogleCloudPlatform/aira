
import { z } from "zod";

const SchemaAnswer = z.string()

export const SchemaMultipleChoiceAnswer = z.object({
    answers: z.array(SchemaAnswer).min(1, { message: "toast.errors.exam.required_answer" })
});

export const SchemaMultipleChoiceDefaultValues : z.infer<typeof SchemaMultipleChoiceAnswer> = {
    answers: []
}
