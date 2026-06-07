import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2557a7'
    },
    secondary: {
      main: '#2f855a'
    },
    background: {
      default: '#f6f8fb',
      paper: '#ffffff'
    },
    text: {
      primary: '#172033',
      secondary: '#5f6b7a'
    }
  },
  shape: {
    borderRadius: 8
  },
  typography: {
    fontFamily: ['Inter', 'Roboto', 'Arial', 'sans-serif'].join(','),
    h4: {
      fontWeight: 700
    },
    h6: {
      fontWeight: 700
    },
    body2: {
      lineHeight: 1.55
    },
    caption: {
      lineHeight: 1.4
    }
  },
  components: {
    MuiButton: {
      defaultProps: {
        variant: 'contained'
      },
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 700
        }
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: '1px solid #dce3ec',
          boxShadow: '0 1px 2px rgba(18, 25, 38, 0.04)'
        }
      }
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          color: '#334155',
          fontWeight: 800,
          backgroundColor: '#f8fafc'
        },
        root: {
          borderBottom: '1px solid #e8edf5'
        }
      }
    }
  }
});
