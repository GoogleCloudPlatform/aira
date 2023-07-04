export const selectStyle = {
    control: (baseStyles : any, state : any) => ({
        ...baseStyles,
        borderColor: 'bg-gray-200',
        color: '#9ca3af',
        backgroundColor: state.isDisabled ? '#fafafa' : '',
        '&:hover': {
            cursor: "pointer"
        },
    }),
    menu: (baseStyles : any, state : any) => ({
        ...baseStyles,
        cursor: "pointer",
        zIndex: 100,
        //position: "relative"
    }),
    menuList: (baseStyles : any, state : any) => ({
        ...baseStyles,
        maxHeight: '120px',
        zIndex: 100,
        position: "relative",
        cursor: "pointer",
        color: '#6b7280',
    }),
    option: (baseStyles : any, state : any) => ({
        ...baseStyles,
        cursor: "pointer"
    }),
    singleValue: (baseStyles : any, state : any) => ({
        ...baseStyles,
        color: "#6b7280"
    }),
    valueContainer: (baseStyles : any, state : any) => ({
        ...baseStyles,
        maxHeight: "40px",
        overflowY: "auto",
        /* Hide scrollbar for Chrome, Safari and Opera */
        '&::-webkit-scrollbar': {
            display: 'none',
        },
        /* Hide scrollbar for IE, Edge and Firefox */
        'msOverflowStyle': 'none', /* IE and Edge */
        'scrollbarWidth': 'none', /* Firefox */
    }),
}