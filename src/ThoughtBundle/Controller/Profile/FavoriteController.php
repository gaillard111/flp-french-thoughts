<?php

namespace ThoughtBundle\Controller\Profile;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\OptimisticLockException;
use Knp\Component\Pager\Pagination\PaginationInterface;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\StreamedResponse;
use ThoughtBundle\Entity\Thought;
use Symfony\Component\Routing\Annotation\Route;

/**
 * @Route("/profile")
 */
class FavoriteController extends Controller
{
    /**
     * @Route("/favorite", name="favorite-list")
     */
    public function favoriteQuotesAction(Request $request)
    {
        /** @var PaginationInterface $paginator */
        $paginator = $this->get('knp_paginator');

        $likedThoughts = $this->getDoctrine()
            ->getRepository(Thought::class)
            ->getLikedThoughts($this->getUser());

        $pagination = $paginator->paginate(
            $likedThoughts,
            $request->query->getInt('page', 1),
            20
        );

        return $this->render('@Thought/Profile/favorite_list.html.twig', [
            'thoughts_pagination' => $pagination,
        ]);
    }

    /**
     * @Route("/most-favorite/add/{thoughtId}", name="add_to_most_favorites")
     *
     * @param int $thoughtId
     *
     * @return JsonResponse
     *
     * @throws OptimisticLockException
     */
    public function ajaxAddToMostFavorites($thoughtId)
    {
        $em = $this->get('doctrine.orm.entity_manager');
        /** @var Thought $thought */
        $thought = $em->getRepository(Thought::class)->find($thoughtId);
        /** @var User $user */
        $user = $this->getUser();

        $userThoughts = $user->getMostFavoriteThoughts();

        if ($userThoughts->contains($thought)) {
            return new JsonResponse(['result' => 'already exists'], 400);
        }
        $user->addThoughtToMostFavorite($thought);
        $em->persist($user);
        $em->flush();
        return new JsonResponse(['result' => 'success'], 200);
    }

    /**
     * @Route("/most-favorite/delete/{thoughtId}", name="delete_from_most_favorites")
     *
     * @param $thoughtId
     *
     * @return JsonResponse
     *
     * @throws OptimisticLockException
     */
    public function ajaxDeleteFromMostFavorites($thoughtId)
    {
        $em = $this->get('doctrine.orm.entity_manager');
        /** @var Thought $thought */
        $thought = $em->getRepository(Thought::class)->find($thoughtId);
        /** @var User $user */
        $user = $this->getUser();

        $userThoughts = $user->getMostFavoriteThoughts();

        if (!$userThoughts->contains($thought)) {
            return new JsonResponse(['result' => 'Not found'], 404);
        }

        $user->deleteThoughtFromMostFavorites($thought);
        $em->persist($user);
        $em->flush();
        return new JsonResponse(['result' => 'success'], 200);
    }

    /**
     * @Route("favorite/export", name="export-favorite-quotes")
     */
    public function exportFavoriteToCsvAction()
    {
        $likedThoughts = $this->getDoctrine()->getRepository(Thought::class)->getLikedThoughts($this->getUser())->getResult();
        $response      = new StreamedResponse();

        $response->setCallback(function () use ($likedThoughts) {
            $handle = fopen('php://output', 'w+');

            fputcsv($handle, ['Citation', 'Auteur', 'Catégorie', 'Created'], ',');

            /** @var Thought[] $likedThoughts */
            foreach ($likedThoughts as $thought) {
                fputcsv($handle, [$thought->getContent(), $thought->getAuthor(), $thought->getCategory(), $thought->getCreatedAt()->format('d.m.Y H:i')], ',');
            }

            fclose($handle);
        });

        $response->setStatusCode(200);
        $response->headers->set('Content-Type', 'text/csv; charset=utf-8');
        $response->headers->set('Content-Disposition', 'attachment; filename="export.csv"');
        return $response;
    }


}