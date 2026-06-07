import { Box, Typography } from '@mui/material';

type PageHeaderProps = {
  title: string;
  description: string;
};

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <Box sx={{ mb: 3 }}>
      <Typography component="h1" variant="h4">
        {title}
      </Typography>
      <Typography color="text.secondary" sx={{ mt: 0.75 }} variant="body1">
        {description}
      </Typography>
    </Box>
  );
}
