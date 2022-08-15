<?php

namespace AdminBundle\Controller;

use Application\Sonata\UserBundle\Entity\User;
use Sonata\AdminBundle\Controller\CRUDController;
use Symfony\Component\HttpFoundation\ResponseHeaderBag;
use Symfony\Component\HttpFoundation\StreamedResponse;

class UserActionsController extends CRUDController
{

    private $genders = [
        null => '',
        'm' => 'Male',
        'f' => 'Female'
    ];

    public function userExportAction(User $user)
    {
        $response = new StreamedResponse();

        $response->setCallback(function () use ($user) {

            $handle = fopen('php://output', 'r+');

            // Header
            fputcsv($handle, ['First Name', 'Last Name', 'User Name', 'Email', 'Registration date', 'Gender', 'Country', 'Interests', 'About', 'Receive Emails']);

            fputcsv($handle, [
                'f_name' => $user->getFirstname(),
                'l_name' => $user->getLastname(),
                'user_name' => $user->getUsername(),
                'email' => $user->getEmail(),
                'reg_at' => $user->getCreatedAt()->format('Y-m-d H:i:s'),
                'gender' => $this->genders[$user->getGender()],
                'country' => $user->getCountry(),
                'interests' => $user->getInterests(),
                'about' => $user->getAbout(),
                'receive_emails' => $user->isReceiveEmails() ? 'Yes' : 'No'
            ]);

            fclose($handle);
        });

        $disposition = $response->headers->makeDisposition(ResponseHeaderBag::DISPOSITION_ATTACHMENT, 'user.csv');
        $response->headers->set('Content-Disposition', $disposition);
        $response->headers->set('Content-Type', 'text/csv; charset=utf-8');

        return $response;
    }
}