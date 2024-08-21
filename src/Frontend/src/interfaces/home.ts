interface HomeProps {
  //name: string | undefined;
}

interface ActionProps {
    name: string;
    icon?: React.ReactNode;
    label: string;
    route: string;
    data: any;
    classes?: {
      icon_container: string,
    }
}

interface SectionsProps {
    type: string,
    actions: ActionProps[]
}

interface UserProps {
    type: string;
    label: string;
    render: boolean;
    permissions: string[];
    actions: ActionProps[];
}